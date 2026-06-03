import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { rentalsApi } from '../../api/contracts'
import { capitalizar, formatoMoneda } from '../../utils/constants'
import { useLookups } from '../../hooks/useLookups'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

const ESTADOS = ['pendiente', 'en revision', 'aprobada', 'rechazada', 'cancelada']

function GenerarContrato({ solicitud, precioPublicado, onDone }) {
  // Fechas y precio precargados; el administrador puede modificarlos y agregar observaciones.
  const [form, setForm] = useState({
    fecha_inicio: solicitud.fecha_inicio || '',
    fecha_fin: solicitud.fecha_fin || '',
    monto: precioPublicado || '',
    condiciones: '',
  })
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const set = (f) => (e) => setForm((s) => ({ ...s, [f]: e.target.value }))

  async function generar(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    try {
      await rentalsApi.generarContrato(solicitud.id, {
        fecha_inicio: form.fecha_inicio, fecha_fin: form.fecha_fin,
        monto: Number(form.monto), condiciones: form.condiciones || null,
      })
      setMsg({ ok: 'Contrato generado; el inmueble pasó a rentado.', err: '' })
      onDone()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo generar el contrato.' }) }
  }

  return (
    <form onSubmit={generar} className="stack" aria-label={`Generar contrato de la solicitud ${solicitud.id}`}>
      <p style={{ margin: 0 }}><strong>Aprobar y generar contrato</strong> (acepta o modifica las fechas y el precio):</p>
      <div className="grid form-2">
        <Field label="Inicio" type="date" value={form.fecha_inicio} onChange={set('fecha_inicio')} required />
        <Field label="Fin" type="date" value={form.fecha_fin} onChange={set('fecha_fin')} required />
        <Field label="Renta mensual" type="number" min="0" value={form.monto} onChange={set('monto')} required
               hint={precioPublicado ? `Precio publicado: ${formatoMoneda(precioPublicado)}` : undefined} />
      </div>
      <Field label="Observaciones / condiciones especiales" as="textarea" value={form.condiciones} onChange={set('condiciones')} />
      <button className="btn" type="submit">Generar contrato</button>
      {msg.err && <span className="error-text">{msg.err}</span>}
      {msg.ok && <span style={{ color: 'var(--color-success)' }}>{msg.ok}</span>}
    </form>
  )
}

function GenerarContratoVenta({ solicitud, precioPublicado, onDone }) {
  const [form, setForm] = useState({ monto: precioPublicado || '', condiciones: '' })
  const [msg, setMsg] = useState({ ok: '', err: '' })
  async function generar(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    try {
      await rentalsApi.generarContratoVenta(solicitud.id, { monto: Number(form.monto), condiciones: form.condiciones || null })
      setMsg({ ok: 'Contrato de venta generado; el inmueble pasó a reservado.', err: '' })
      onDone()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo generar el contrato.' }) }
  }
  return (
    <form onSubmit={generar} className="stack" aria-label={`Generar contrato de venta ${solicitud.id}`}>
      <p style={{ margin: 0 }}><strong>Aprobar y generar contrato de compraventa</strong> (confirma o modifica el precio):</p>
      <div className="grid form-2">
        <Field label="Precio de venta" type="number" min="0" value={form.monto} onChange={(e) => setForm((s) => ({ ...s, monto: e.target.value }))} required
               hint={precioPublicado ? `Precio publicado: ${formatoMoneda(precioPublicado)}` : undefined} />
      </div>
      <Field label="Observaciones / condiciones especiales" as="textarea" value={form.condiciones} onChange={(e) => setForm((s) => ({ ...s, condiciones: e.target.value }))} />
      <button className="btn" type="submit">Generar contrato de venta</button>
      {msg.err && <span className="error-text">{msg.err}</span>}
      {msg.ok && <span style={{ color: 'var(--color-success)' }}>{msg.ok}</span>}
    </form>
  )
}

export default function RequestsAdmin() {
  const [solicitudes, setSolicitudes] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const { users, props, propLabel } = useLookups(
    solicitudes.map((s) => s.usuario_id), solicitudes.map((s) => s.inmueble_id),
  )

  async function cargar() {
    setLoading(true)
    try { setSolicitudes(await rentalsApi.all()) }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar las solicitudes.' }) }
    finally { setLoading(false) }
  }
  useEffect(() => { cargar() }, [])

  async function cambiarEstado(s, estado) {
    setMsg({ ok: '', err: '' })
    try { await rentalsApi.setEstado(s.id, estado); cargar() }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo actualizar.' }) }
  }

  if (loading) return <Spinner />

  return (
    <div className="stack">
      <h1>Solicitudes de renta y compra</h1>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      {solicitudes.length === 0 ? (
        <p className="muted">No hay solicitudes.</p>
      ) : (
        solicitudes.map((s) => {
          const cliente = users[s.usuario_id]
          const inm = props[s.inmueble_id]
          return (
            <div key={s.id} className="card stack">
              <div className="row" style={{ justifyContent: 'space-between' }}>
                <h3 style={{ margin: 0 }}>Solicitud #{s.id} — {s.tipo_operacion === 'venta' ? 'Compra' : 'Renta'}</h3>
                <span className="badge">{capitalizar(s.estado)}</span>
              </div>

              {/* Información completa del cliente y del inmueble */}
              <div className="grid form-2">
                <div className="card" style={{ background: '#faf8ff' }}>
                  <h4 style={{ margin: '0 0 .3rem' }}>Cliente</h4>
                  <p className="muted" style={{ margin: 0 }}>
                    {cliente ? <>{cliente.nombre}<br />{cliente.correo}<br />Tel: {cliente.telefono || '—'}</> : `Cliente #${s.usuario_id}`}
                  </p>
                </div>
                <div className="card" style={{ background: '#faf8ff' }}>
                  <h4 style={{ margin: '0 0 .3rem' }}>Inmueble</h4>
                  <p className="muted" style={{ margin: 0 }}>
                    <Link to={`/inmueble/${s.inmueble_id}`}>{propLabel(s.inmueble_id)}</Link>
                    {inm && <><br />{capitalizar(inm.tipo)} · {capitalizar(inm.uso)}<br /><strong>Precio publicado: {formatoMoneda(inm.precio)}/mes</strong></>}
                  </p>
                </div>
              </div>

              <p className="muted" style={{ margin: 0 }}>
                <strong>Fechas solicitadas:</strong> {s.fecha_inicio || '—'} → {s.fecha_fin || '—'}
                {s.duracion_meses ? ` · ${s.duracion_meses} mes(es)` : ''}
                {s.mensaje ? ` · Nota: "${s.mensaje}"` : ''}
              </p>

              <div className="row">
                <label className="sr-only" htmlFor={`est-${s.id}`}>Estado de la solicitud {s.id}</label>
                <select id={`est-${s.id}`} value={s.estado} onChange={(e) => cambiarEstado(s, e.target.value)}>
                  {ESTADOS.map((e) => <option key={e} value={e}>{capitalizar(e)}</option>)}
                </select>
              </div>

              {s.estado === 'aprobada' && !s.contrato_id && (
                s.tipo_operacion === 'venta'
                  ? <GenerarContratoVenta solicitud={s} precioPublicado={inm?.precio} onDone={cargar} />
                  : <GenerarContrato solicitud={s} precioPublicado={inm?.precio} onDone={cargar} />
              )}
              {s.contrato_id && <p className="muted" style={{ margin: 0 }}>Contrato generado: #{s.contrato_id}</p>}
            </div>
          )
        })
      )}
    </div>
  )
}
