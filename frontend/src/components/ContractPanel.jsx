import { useEffect, useState } from 'react'
import { contractsApi, descargarBlob } from '../api/contracts'
import { formatoMoneda, capitalizar } from '../utils/constants'
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
  const [metodo, setMetodo] = useState('efectivo')   // efectivo | transferencia | tarjeta
  const [montoVenta, setMontoVenta] = useState('')
  const [archivo, setArchivo] = useState(null)
  const [comprobantePago, setComprobantePago] = useState(null)
  const [cuotaSel, setCuotaSel] = useState('')
  const [conceptoVenta, setConceptoVenta] = useState('cuota')  // venta a plazos: 'cuota' | 'abono'
  const [motivoRechazo, setMotivoRechazo] = useState('')
  const [msg, setMsg] = useState({ ok: '', err: '' })

  const esRenta = datos.tipo === 'Renta'
  // Solo se puede pagar cuando el contrato está firmado y validado por el admin.
  const puedePagar = Boolean(datos.url_firmado) && datos.estado_documento === 'aprobado'
  // Mensualidades que aún se pueden cubrir (pendientes o atrasadas), ordenadas por número.
  const cuotasPagables = pagos
    .filter((p) => ['pendiente', 'vencido'].includes(p.estado) && p.numero_cuota)
    .sort((a, b) => (a.numero_cuota || 0) - (b.numero_cuota || 0))
  // ¿El contrato tiene calendario de mensualidades? (renta o venta a plazos)
  const hayCalendario = pagos.some((p) => p.numero_cuota)
  const ventaAPlazos = !esRenta && hayCalendario
  // Se paga por cuota cuando es renta, o venta a plazos con concepto "cuota".
  const usaCuota = esRenta || (ventaAPlazos && conceptoVenta === 'cuota')
  const cuotaActual = usaCuota
    ? (cuotasPagables.find((c) => String(c.numero_cuota) === String(cuotaSel)) || cuotasPagables[0])
    : null
  const montoAPagar = usaCuota ? Number(cuotaActual?.monto || 0) : Number(montoVenta || 0)
  const numeroCuotaAPagar = usaCuota ? cuotaActual?.numero_cuota : undefined
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
    // Si ya hay un firmado cargado (y no validado), confirmar el reemplazo.
    if (datos.url_firmado && !window.confirm(
      'Ya existe un documento firmado. El archivo anterior será reemplazado por el nuevo. ¿Continuar?'
    )) return
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
  async function pagar(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    const monto = montoAPagar
    const numeroCuota = numeroCuotaAPagar
    if (!monto || monto <= 0) { setMsg({ ok: '', err: 'Indica un monto válido a pagar.' }); return }
    try {
      if (metodo === 'transferencia') {
        if (!comprobantePago) { setMsg({ ok: '', err: 'Adjunta el comprobante de la transferencia.' }); return }
        await contractsApi.addPaymentTransferencia(contrato.id, monto, comprobantePago, numeroCuota)
        setComprobantePago(null)
      } else {
        await contractsApi.addPayment(contrato.id, { monto, metodo: 'efectivo', numero_cuota: numeroCuota })
      }
      setMontoVenta(''); setCuotaSel('')
      setMsg({ ok: 'Pago registrado. Quedó pendiente de verificación; el administrador lo revisará en breve.', err: '' })
      refrescar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo registrar el pago. Intenta de nuevo.' }) }
  }

  // Verificación de pagos manuales por el administrador.
  async function verificarPago(pagoId, aprobado) {
    setMsg({ ok: '', err: '' })
    let motivo = null
    if (!aprobado) {
      motivo = window.prompt('Motivo del rechazo del pago:')
      if (motivo === null) return
    }
    try {
      await contractsApi.verificarPago(pagoId, { aprobado, motivo })
      setMsg({ ok: aprobado ? 'Pago aprobado.' : 'Pago rechazado.', err: '' }); refrescar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo verificar el pago.' }) }
  }

  // Recibe el payment_method generado por Stripe Elements (datos reales de tarjeta).
  async function pagarStripe(paymentMethodId) {
    setMsg({ ok: '', err: '' })
    const monto = montoAPagar
    if (!monto || monto <= 0) { setMsg({ ok: '', err: 'Indica un monto válido a pagar.' }); throw new Error('monto') }
    const p = await contractsApi.pagarStripe(contrato.id, { monto, payment_method: paymentMethodId, numero_cuota: numeroCuotaAPagar })
    setMontoVenta(''); setCuotaSel('')
    setMsg({ ok: `¡Pago con tarjeta aprobado! Referencia: ${p.stripe_payment_intent}.`, err: '' })
    refrescar()
  }

  // --- Acciones de administrador ---
  async function cambiarEstado(nuevo) {
    if (nuevo === datos.estado) return
    // Confirmación para evitar cambios accidentales que afecten el proceso administrativo.
    if (!window.confirm(`¿Cambiar el estado del contrato de "${etiquetaEstado(datos.estado)}" a "${etiquetaEstado(nuevo)}"?`)) {
      refrescar()  // restablece el select al valor real
      return
    }
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
  const etiquetaPago = (e) => capitalizar((e || '').replace(/_/g, ' '))
  // Describe a qué pago/concepto pertenece un comprobante (mensualidad, abono, renta/venta).
  function descripcionPago(pagoId) {
    const op = esRenta ? 'renta' : 'venta'
    if (!pagoId) return `Pago de ${op}`
    const p = pagos.find((x) => x.id === pagoId)
    if (!p) return `Pago #${pagoId} de ${op}`
    const concepto = p.numero_cuota
      ? `Mensualidad ${p.numero_cuota}${p.fecha_vencimiento ? ` (vence ${p.fecha_vencimiento})` : ''}`
      : (esRenta ? 'Mensualidad de renta' : 'Abono a capital')
    return `${concepto} · ${formatoMoneda(p.monto)} · ${op} ${datos.folio || '#' + contrato.id} · pago #${pagoId} (${etiquetaPago(p.estado)})`
  }
  // Columna de verificación (solo admin, solo pagos pendientes de verificación).
  const colVerificar = {
    key: 'verif', header: 'Verificación',
    render: (r) => (admin && r.estado === 'pendiente_de_verificacion' ? (
      <span className="row">
        <button className="btn small" type="button" onClick={() => verificarPago(r.id, true)}>Aprobar</button>
        <button className="btn small danger" type="button" onClick={() => verificarPago(r.id, false)}>Rechazar</button>
      </span>
    ) : '—'),
  }
  const colsRenta = [
    { key: 'numero_cuota', header: 'Cuota' },
    { key: 'fecha_vencimiento', header: 'Vence' },
    { key: 'monto', header: 'Monto', render: (r) => formatoMoneda(r.monto) },
    { key: 'metodo', header: 'Método', render: (r) => r.metodo || '—' },
    { key: 'estado', header: 'Estado', render: (r) => etiquetaPago(r.estado) },
    colVerificar,
  ]
  const colsVenta = [
    { key: 'fecha', header: 'Fecha', render: (r) => (r.fecha ? new Date(r.fecha).toLocaleString('es-MX') : '—') },
    { key: 'monto', header: 'Monto', render: (r) => formatoMoneda(r.monto) },
    { key: 'metodo', header: 'Método', render: (r) => r.metodo || '—' },
    { key: 'estado', header: 'Estado', render: (r) => etiquetaPago(r.estado) },
    { key: 'tx', header: 'Transacción', render: (r) => r.stripe_payment_intent || '—' },
    colVerificar,
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
        Documentación firmada: <strong>{etiquetaEstado(datos.estado_documento)}</strong>
        {datos.motivo_rechazo ? ` — motivo del rechazo: ${datos.motivo_rechazo}` : ''}
      </p>
      {datos.estado_documento === 'rechazado' && !admin && (
        <Alert type="error">
          Tu documento firmado fue rechazado{datos.motivo_rechazo ? `: ${datos.motivo_rechazo}` : '.'} Sube
          una versión corregida más abajo para que el administrador la revise de nuevo.
        </Alert>
      )}

      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      <div className="row" style={{ alignItems: 'center' }}>
        <button className="btn small" type="button" onClick={descargarPdf}>Descargar contrato (PDF)</button>
        {datos.url_firmado ? (
          <button className="btn small secondary" type="button" onClick={descargarFirmado}>Descargar firmado</button>
        ) : (
          <button className="btn small secondary" type="button" disabled title="Aún no se ha subido el documento firmado">
            Descargar firmado (no disponible)
          </button>
        )}
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

      {/* El documento firmado se puede subir/reemplazar solo si NO ha sido aprobado y el
          contrato sigue abierto. Si fue rechazado o está pendiente, se permite reemplazar. */}
      {datos.estado_documento === 'aprobado' ? (
        <p className="muted">La documentación firmada ya fue aprobada; no puede reemplazarse.</p>
      ) : ['cancelado', 'finalizado', 'liquidado'].includes(datos.estado) ? (
        <p className="muted">El contrato está {etiquetaEstado(datos.estado)}; el documento firmado ya no puede modificarse.</p>
      ) : (
        <form onSubmit={subirFirmado} className="row" aria-label="Subir contrato firmado">
          <div className="field" style={{ marginBottom: 0 }}>
            <label htmlFor={`firma-${contrato.id}`}>
              {datos.url_firmado ? 'Reemplazar contrato firmado (PDF/imagen)' : 'Subir contrato firmado (PDF/imagen)'}
            </label>
            <input id={`firma-${contrato.id}`} type="file" accept="application/pdf,image/png,image/jpeg" onChange={(e) => setArchivo(e.target.files[0])} />
          </div>
          <button className="btn small secondary" type="submit" disabled={!archivo}>
            {datos.url_firmado ? 'Reemplazar' : 'Subir'}
          </button>
        </form>
      )}

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
        caption={hayCalendario ? 'Calendario de pagos (mensual)' : 'Historial de pagos'}
        columns={hayCalendario ? colsRenta : colsVenta} rows={pagos} empty="Sin pagos registrados."
      />

      {/* Contrato no activo (finalizado/cancelado/liquidado): no se aceptan pagos. */}
      {datos.estado !== 'activo' && (
        <Alert type="info">
          Este contrato está <strong>{etiquetaEstado(datos.estado)}</strong>; no se pueden registrar más pagos.
        </Alert>
      )}

      {/* Los pagos solo se habilitan con el contrato firmado y validado. */}
      {datos.estado === 'activo' && !puedePagar && (
        <Alert type="info">
          Los pagos se habilitarán cuando el contrato esté firmado por las partes y la
          documentación haya sido validada por el administrador.
        </Alert>
      )}

      {/* Al corriente: sin mensualidades por cubrir (renta o venta a plazos), y sin abono libre disponible. */}
      {datos.estado === 'activo' && puedePagar && esRenta && cuotasPagables.length === 0 && (
        <Alert type="success">La renta está al corriente: no hay mensualidades pendientes.</Alert>
      )}

      {datos.estado === 'activo' && puedePagar && !(esRenta && cuotasPagables.length === 0) && (
        <div className="card stack" aria-label="Registrar un pago">
          <h4 style={{ margin: 0 }}>Registrar un pago</h4>

          {/* Paso 1 — Concepto. Renta y venta a plazos eligen mensualidad; venta permite abono a capital. */}
          {(esRenta || ventaAPlazos) && (
            <Field label="¿Qué deseas cubrir?" as="select"
                   value={ventaAPlazos ? conceptoVenta : 'cuota'}
                   onChange={(e) => setConceptoVenta(e.target.value)}
                   options={ventaAPlazos
                     ? [{ value: 'cuota', label: 'Una mensualidad' }, { value: 'abono', label: 'Abono a capital (monto libre)' }]
                     : [{ value: 'cuota', label: 'Una mensualidad' }]} />
          )}

          {usaCuota && cuotasPagables.length > 0 && (
            <Field label="Mensualidad a cubrir" as="select"
                   value={cuotaSel || (cuotaActual?.numero_cuota ?? '')}
                   onChange={(e) => setCuotaSel(e.target.value)}
                   options={cuotasPagables.map((c) => ({
                     value: c.numero_cuota,
                     label: `Mensualidad ${c.numero_cuota} · vence ${c.fecha_vencimiento} · ${formatoMoneda(c.monto)}${c.estado === 'vencido' ? ' (atrasada)' : ''}`,
                   }))}
                   hint="Puedes pagar la más próxima o ponerte al corriente con una atrasada." />
          )}

          {!usaCuota && (
            <Field label="Monto a abonar (MXN)" type="number" min="0" step="0.01" value={montoVenta}
                   onChange={(e) => setMontoVenta(e.target.value)} required
                   hint={`Saldo pendiente: ${formatoMoneda(resumen?.saldo_pendiente ?? datos.monto)}`} />
          )}

          <p className="muted" style={{ margin: 0 }}>
            Concepto: <strong>
              {usaCuota
                ? `Mensualidad ${cuotaActual?.numero_cuota ?? '—'}`
                : (esRenta ? 'Mensualidad de renta' : 'Abono a cuenta del precio de venta')}
            </strong> · Importe a pagar: <strong>{formatoMoneda(montoAPagar)}</strong>
          </p>

          {/* Paso 2 — Método de pago: se elige uno y solo se muestran sus campos. */}
          <Field label="Método de pago" as="select" value={metodo} onChange={(e) => setMetodo(e.target.value)}
                 options={[
                   { value: 'efectivo', label: 'Efectivo' },
                   { value: 'transferencia', label: 'Transferencia' },
                   { value: 'tarjeta', label: 'Tarjeta (Stripe)' },
                 ]} />

          {metodo === 'efectivo' && (
            <form onSubmit={pagar} className="stack">
              <p className="muted" style={{ margin: 0 }}>
                El pago en efectivo queda <strong>pendiente de verificación</strong> hasta que el administrador lo confirme.
              </p>
              <button className="btn" type="submit">Registrar pago en efectivo</button>
            </form>
          )}

          {metodo === 'transferencia' && (
            <form onSubmit={pagar} className="stack">
              <p className="muted" style={{ margin: 0 }}>
                Adjunta el comprobante. El pago queda <strong>pendiente de verificación</strong> hasta que el administrador lo confirme.
              </p>
              <div className="field" style={{ marginBottom: 0 }}>
                <label htmlFor={`comppago-${contrato.id}`}>Comprobante (PDF o imagen)</label>
                <input id={`comppago-${contrato.id}`} type="file" accept="application/pdf,image/png,image/jpeg"
                       onChange={(e) => setComprobantePago(e.target.files[0])} />
              </div>
              <button className="btn" type="submit" disabled={!comprobantePago}>Registrar transferencia</button>
            </form>
          )}

          {metodo === 'tarjeta' && (
            montoAPagar < 10 ? (
              <Alert type="info">
                El pago con tarjeta requiere al menos $10.00 MXN. Para este importe
                ({formatoMoneda(montoAPagar)}) usa efectivo o transferencia.
              </Alert>
            ) : (
              <StripeCardForm monto={montoAPagar} onPay={pagarStripe} />
            )
          )}
        </div>
      )}

      {/* Los comprobantes se generan al pagar por transferencia (van ligados a su pago);
          aquí solo se listan, no se suben sueltos. */}
      <div className="stack">
        <h4 style={{ margin: 0 }}>Comprobantes de pago</h4>
        {comprobantes.length === 0 ? (
          <p className="muted" style={{ margin: 0 }}>Aún no hay comprobantes. Se adjuntan al registrar un pago por transferencia.</p>
        ) : (
          <ul>
            {comprobantes.map((c) => (
              <li key={c.id}>
                {new Date(c.fecha_carga).toLocaleDateString('es-MX')} — {userLabel(c.usuario_id)}
                {' · '}<strong>{descripcionPago(c.pago_id)}</strong>{' '}
                <button className="btn small secondary" type="button" onClick={() => descargarComprobante(c.id)}>Descargar</button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
