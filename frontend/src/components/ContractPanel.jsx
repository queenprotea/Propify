import { useEffect, useState } from 'react'
import { contractsApi, descargarBlob } from '../api/contracts'
import { METODOS_PAGO, formatoMoneda, capitalizar } from '../utils/constants'
import { useLookups } from '../hooks/useLookups'
import Field from './Field'
import Alert from './Alert'
import DataTable from './DataTable'
import StripeCardForm from './StripeCardForm'

const ESTADOS_CONTRATO = ['borrador', 'pendiente_de_firma', 'firmado', 'activo', 'finalizado', 'cancelado', 'liquidado']
const etiquetaEstado = (e) => capitalizar((e || '').replace(/_/g, ' '))

// Panel con todas las acciones sobre un contrato. Reutilizado por cliente y admin.
export default function ContractPanel({ contrato, admin = false }) {
  const [pagos, setPagos] = useState([])
  const [resumen, setResumen] = useState(null)
  const [comprobantes, setComprobantes] = useState([])
  const [datos, setDatos] = useState(contrato)
  const [metodo, setMetodo] = useState('transferencia')
  const [montoVenta, setMontoVenta] = useState('')
  const [archivo, setArchivo] = useState(null)
  const [comprobante, setComprobante] = useState(null)
  const [motivoRechazo, setMotivoRechazo] = useState('')
  const [msg, setMsg] = useState({ ok: '', err: '' })

  const esRenta = datos.tipo === 'Renta'
  // Solo se puede pagar cuando el contrato está firmado y validado por el admin.
  const puedePagar = Boolean(datos.url_firmado) && datos.estado_documento === 'aprobado'
  const { userLabel, propLabel } = useLookups([contrato.usuario_id], [contrato.inmueble_id])

  async function refrescar() {
    try {
      setPagos(await contractsApi.payments(contrato.id))
      setResumen(await contractsApi.resumen(contrato.id))
      setComprobantes(await contractsApi.comprobantes(contrato.id))
      setDatos(await contractsApi.get(contrato.id))
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cargar el contrato.' })
    }
  }
  useEffect(() => {
    refrescar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [contrato.id])

  async function descargarPdf() {
    try { descargarBlob(await contractsApi.pdfBlob(contrato.id), `${datos.folio || 'contrato'}.pdf`) }
    catch { setMsg({ ok: '', err: 'No se pudo descargar el PDF.' }) }
  }
  async function descargarFirmado() {
    try { descargarBlob(await contractsApi.signedBlob(contrato.id), `${datos.folio || 'contrato'}_firmado.pdf`) }
    catch { setMsg({ ok: '', err: 'No se pudo descargar el firmado.' }) }
  }
  async function subirFirmado(e) {
    e.preventDefault()
    if (!archivo) return
    setMsg({ ok: '', err: '' })
    try {
      await contractsApi.uploadSigned(contrato.id, archivo)
      setArchivo(null); setMsg({ ok: 'Contrato firmado subido.', err: '' }); refrescar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo subir el firmado.' }) }
  }
  async function descargarComprobante(id) {
    try { descargarBlob(await contractsApi.comprobanteBlob(id), `comprobante_${id}.pdf`) }
    catch { setMsg({ ok: '', err: 'No se pudo descargar el comprobante.' }) }
  }
  async function subirComprobante(e) {
    e.preventDefault()
    if (!comprobante) return
    setMsg({ ok: '', err: '' })
    try {
      await contractsApi.uploadComprobante(contrato.id, comprobante)
      setComprobante(null); setMsg({ ok: 'Comprobante subido.', err: '' }); refrescar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo subir el comprobante.' }) }
  }
  async function pagar(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    try {
      await contractsApi.addPayment(contrato.id, esRenta ? { monto: datos.monto, metodo } : { monto: Number(montoVenta), metodo })
      setMontoVenta(''); setMsg({ ok: 'Pago registrado.', err: '' }); refrescar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo registrar el pago.' }) }
  }

  // Recibe el payment_method generado por Stripe Elements (datos reales de tarjeta).
  async function pagarStripe(paymentMethodId) {
    setMsg({ ok: '', err: '' })
    const monto = esRenta ? Number(datos.monto) : Number(montoVenta)
    if (!monto || monto <= 0) { setMsg({ ok: '', err: 'Indica el monto a pagar.' }); throw new Error('monto') }
    const p = await contractsApi.pagarStripe(contrato.id, { monto, payment_method: paymentMethodId })
    setMontoVenta('')
    setMsg({ ok: `Pago con tarjeta procesado (transacción ${p.stripe_payment_intent}).`, err: '' })
    refrescar()
  }

  // --- Acciones de administrador ---
  async function cambiarEstado(nuevo) {
    setMsg({ ok: '', err: '' })
    try { await contractsApi.setEstado(contrato.id, nuevo); setMsg({ ok: 'Estado actualizado.', err: '' }); refrescar() }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cambiar el estado.' }) }
  }
  async function validarDoc(aprobado) {
    setMsg({ ok: '', err: '' })
    try {
      await contractsApi.validarDocumento(contrato.id, { aprobado, motivo: aprobado ? null : motivoRechazo })
      setMotivoRechazo(''); setMsg({ ok: aprobado ? 'Documento aprobado.' : 'Documento rechazado.', err: '' }); refrescar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo validar el documento.' }) }
  }
  const colsRenta = [
    { key: 'numero_cuota', header: 'Cuota' },
    { key: 'fecha_vencimiento', header: 'Vence' },
    { key: 'monto', header: 'Monto', render: (r) => formatoMoneda(r.monto) },
    { key: 'estado', header: 'Estado', render: (r) => capitalizar(r.estado) },
  ]
  const colsVenta = [
    { key: 'fecha', header: 'Fecha', render: (r) => (r.fecha ? new Date(r.fecha).toLocaleString('es-MX') : '—') },
    { key: 'monto', header: 'Monto', render: (r) => formatoMoneda(r.monto) },
    { key: 'metodo', header: 'Método', render: (r) => r.metodo || '—' },
    { key: 'estado', header: 'Estado', render: (r) => capitalizar(r.estado) },
    { key: 'tx', header: 'Transacción', render: (r) => r.stripe_payment_intent || '—' },
  ]

  return (
    <div className="card stack">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h3 style={{ margin: 0 }}>{datos.folio || `Contrato #${contrato.id}`} — {datos.tipo}</h3>
        <span className="badge">{etiquetaEstado(datos.estado)}</span>
      </div>
      <p className="muted" style={{ margin: 0 }}>
        <strong>Cliente:</strong> {userLabel(contrato.usuario_id)}<br />
        <strong>Inmueble:</strong> {propLabel(contrato.inmueble_id)}<br />
        <strong>Vigencia:</strong> {datos.fecha_inicio} {datos.fecha_fin ? `→ ${datos.fecha_fin}` : ''} · {formatoMoneda(datos.monto)}
      </p>
      <p className="muted" style={{ margin: 0 }}>
        Documentación firmada: <strong>{capitalizar(datos.estado_documento)}</strong>
        {datos.motivo_rechazo ? ` — motivo: ${datos.motivo_rechazo}` : ''}
      </p>

      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      <div className="row">
        <button className="btn small" type="button" onClick={descargarPdf}>Descargar contrato (PDF)</button>
        {datos.url_firmado && <button className="btn small secondary" type="button" onClick={descargarFirmado}>Descargar firmado</button>}
      </div>

      {/* Acciones de administrador: estado y validación de documentación */}
      {admin && (
        <div className="card" style={{ background: '#faf8ff' }}>
          <div className="row" style={{ alignItems: 'end' }}>
            <Field label="Cambiar estado" as="select"
                   options={ESTADOS_CONTRATO.map((e) => ({ value: e, label: etiquetaEstado(e) }))}
                   value={datos.estado} onChange={(e) => cambiarEstado(e.target.value)} />
          </div>
          {datos.url_firmado && datos.estado_documento === 'pendiente' && (
            <div className="stack" style={{ marginTop: '0.5rem' }}>
              <p style={{ margin: 0 }}><strong>Validar documentación firmada:</strong></p>
              <div className="row">
                <button className="btn small" type="button" onClick={() => validarDoc(true)}>Aprobar</button>
                <input type="text" placeholder="Motivo del rechazo" value={motivoRechazo}
                       onChange={(e) => setMotivoRechazo(e.target.value)} style={{ flex: 1, minWidth: 180 }} />
                <button className="btn small danger" type="button" disabled={!motivoRechazo.trim()} onClick={() => validarDoc(false)}>Rechazar</button>
              </div>
            </div>
          )}
        </div>
      )}

      <form onSubmit={subirFirmado} className="row" aria-label="Subir contrato firmado">
        <div className="field" style={{ marginBottom: 0 }}>
          <label htmlFor={`firma-${contrato.id}`}>Subir contrato firmado (PDF/imagen)</label>
          <input id={`firma-${contrato.id}`} type="file" accept="application/pdf,image/png,image/jpeg" onChange={(e) => setArchivo(e.target.files[0])} />
        </div>
        <button className="btn small secondary" type="submit" disabled={!archivo}>Subir</button>
      </form>

      {/* Resumen económico (venta y renta) */}
      {resumen && (
        <div className="card" style={{ background: '#f3f7ff' }}>
          <p style={{ margin: 0 }}>
            <strong>Total:</strong> {formatoMoneda(resumen.monto_total)} ·{' '}
            <strong>Pagado:</strong> {formatoMoneda(resumen.total_pagado)} ·{' '}
            <strong>Saldo:</strong> {formatoMoneda(resumen.saldo_pendiente)} ·{' '}
            <strong>{resumen.porcentaje_cubierto}%</strong> cubierto
            {esRenta && resumen.cuotas_pendientes > 0 && ` · ${resumen.cuotas_pendientes} mensualidad(es) pendiente(s)`}
            {resumen.proximo_vencimiento && ` · próximo vencimiento: ${resumen.proximo_vencimiento}`}
            {resumen.liquidado && ' — ✅ Liquidado'}
          </p>
        </div>
      )}

      <DataTable
        caption={esRenta ? 'Calendario de pagos (mensual)' : 'Historial de pagos'}
        columns={esRenta ? colsRenta : colsVenta} rows={pagos} empty="Sin pagos registrados."
      />

      {/* Los pagos solo se habilitan con el contrato firmado y validado. */}
      {datos.estado === 'activo' && !puedePagar && (
        <Alert type="info">
          Los pagos se habilitarán cuando el contrato esté firmado por las partes y la
          documentación haya sido validada por el administrador.
        </Alert>
      )}

      {datos.estado === 'activo' && puedePagar && (
        <div className="stack">
          <form onSubmit={pagar} className="toolbar" aria-label="Registrar pago">
            {!esRenta && (
              <Field label="Monto a pagar (MXN)" type="number" min="0" step="0.01" value={montoVenta} onChange={(e) => setMontoVenta(e.target.value)} required />
            )}
            <Field label="Método" as="select" options={METODOS_PAGO} value={metodo} onChange={(e) => setMetodo(e.target.value)} required />
            <button className="btn" type="submit">{esRenta ? 'Pagar mensualidad' : 'Registrar pago'}</button>
          </form>

          <div className="card" style={{ background: '#f7fbff' }}>
            <p style={{ margin: '0 0 0.5rem' }}><strong>Pago con tarjeta (Stripe)</strong></p>
            {!esRenta && (
              <Field label="Monto a pagar (MXN)" type="number" min="0" step="0.01" value={montoVenta} onChange={(e) => setMontoVenta(e.target.value)} required />
            )}
            <StripeCardForm monto={esRenta ? datos.monto : montoVenta} onPay={pagarStripe} />
          </div>
        </div>
      )}

      <div className="stack">
        <h4 style={{ margin: 0 }}>Comprobantes de pago</h4>
        {comprobantes.length === 0 ? (
          <p className="muted" style={{ margin: 0 }}>Aún no hay comprobantes.</p>
        ) : (
          <ul>
            {comprobantes.map((c) => (
              <li key={c.id}>
                {new Date(c.fecha_carga).toLocaleDateString('es-MX')} — {userLabel(c.usuario_id)}{' '}
                <button className="btn small secondary" type="button" onClick={() => descargarComprobante(c.id)}>Descargar</button>
              </li>
            ))}
          </ul>
        )}
        <form onSubmit={subirComprobante} className="row" aria-label="Subir comprobante de pago">
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor={`comp-${contrato.id}`}>Subir comprobante (PDF/imagen)</label>
            <input id={`comp-${contrato.id}`} type="file" accept="application/pdf,image/png,image/jpeg" onChange={(e) => setComprobante(e.target.files[0])} />
          </div>
          <button className="btn small secondary" type="submit" disabled={!comprobante}>Subir comprobante</button>
        </form>
      </div>
    </div>
  )
}
