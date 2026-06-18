import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { rentalsApi } from '../../api/contracts'
import { capitalizar, formatoMoneda, tipoDe, usoDe, folioSolicitud } from '../../utils/constants'
import { useLookups } from '../../hooks/useLookups'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'
import ClauseSelector from '../../components/ClauseSelector'

const ESTADOS = ['pendiente', 'en revision', 'aprobada', 'rechazada', 'cancelada']

function GenerarContrato({ solicitud, precioPublicado, onDone }) {
  const [form, setForm] = useState({
    fecha_inicio: solicitud.fecha_inicio || '',
    fecha_fin: solicitud.fecha_fin || '',
    monto: precioPublicado || '',
    condiciones: '',
  })
  const [clausulas, setClausulas] = useState([])
  const [clausulasNuevas, setClausulasNuevas] = useState([])
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const set = (f) => (e) => setForm((s) => ({ ...s, [f]: e.target.value }))

  async function generar(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    if (!window.confirm('¿Generar el contrato de renta? El inmueble pasará a "rentado".')) return
    try {
      await rentalsApi.generarContrato(solicitud.id, {
        fecha_inicio: form.fecha_inicio, fecha_fin: form.fecha_fin,
        monto: Number(form.monto), condiciones: form.condiciones || null,
        clausula_ids: clausulas, clausulas_nuevas: clausulasNuevas,
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
        <Field label="Renta mensual" type="number" min="1" max="999999999" value={form.monto} onChange={set('monto')} required
               hint={precioPublicado ? `Precio publicado: ${formatoMoneda(precioPublicado)}` : undefined} />
      </div>
      <Field label="Observaciones / condiciones especiales" as="textarea" value={form.condiciones} onChange={set('condiciones')} maxLength={2000} />
      <ClauseSelector seleccionadas={clausulas} onChange={setClausulas} nuevas={clausulasNuevas} onNuevasChange={setClausulasNuevas} />
      <button className="btn" type="submit">Generar contrato</button>
      {msg.err && <span className="error-text">{msg.err}</span>}
      {msg.ok && <span style={{ color: 'var(--color-success)' }}>{msg.ok}</span>}
    </form>
  )
}

function GenerarContratoVenta({ solicitud, precioPublicado, onDone }) {
  const [form, setForm] = useState({ monto: precioPublicado || '', condiciones: '' })
  const [esquema, setEsquema] = useState('unico')   // 'unico' | 'plazos'
  const [meses, setMeses] = useState('12')
  const [clausulas, setClausulas] = useState([])
  const [clausulasNuevas, setClausulasNuevas] = useState([])
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const mesesPlazo = esquema === 'plazos' ? Math.max(2, Number(meses) || 0) : 1
  async function generar(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    if (esquema === 'plazos' && (mesesPlazo < 2 || mesesPlazo > 120)) {
      setMsg({ ok: '', err: 'El plazo debe estar entre 2 y 120 meses.' }); return
    }
    const detalle = esquema === 'plazos' ? `a ${mesesPlazo} mensualidades` : 'de pago único'
    if (!window.confirm(`¿Generar el contrato de compraventa ${detalle}? El inmueble pasará a "reservado".`)) return
    try {
      await rentalsApi.generarContratoVenta(solicitud.id, {
        monto: Number(form.monto), condiciones: form.condiciones || null,
        clausula_ids: clausulas, clausulas_nuevas: clausulasNuevas, meses_plazo: mesesPlazo,
      })
      setMsg({ ok: 'Contrato de venta generado; el inmueble pasó a reservado.', err: '' })
      onDone()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo generar el contrato.' }) }
  }
  return (
    <form onSubmit={generar} className="stack" aria-label={`Generar contrato de venta ${solicitud.id}`}>
      <p style={{ margin: 0 }}><strong>Aprobar y generar contrato de compraventa</strong> (confirma o modifica el precio):</p>
      <div className="grid form-2">
        <Field label="Precio de venta" type="number" min="1" max="999999999" value={form.monto} onChange={(e) => setForm((s) => ({ ...s, monto: e.target.value }))} required
               hint={precioPublicado ? `Precio publicado: ${formatoMoneda(precioPublicado)}` : undefined} />
        <Field label="Esquema de pago" as="select" value={esquema} onChange={(e) => setEsquema(e.target.value)}
               options={[{ value: 'unico', label: 'Pago único' }, { value: 'plazos', label: 'A plazos (mensualidades)' }]} />
        {esquema === 'plazos' && (
          <Field label="Número de mensualidades" type="number" min="2" max="120" value={meses}
                 onChange={(e) => setMeses(e.target.value)} required
                 hint={form.monto ? `≈ ${formatoMoneda((Number(form.monto) || 0) / mesesPlazo)} por mes` : 'Entre 2 y 120 meses'} />
        )}
      </div>
      <Field label="Observaciones / condiciones especiales" as="textarea" value={form.condiciones} onChange={(e) => setForm((s) => ({ ...s, condiciones: e.target.value }))} maxLength={2000} />
      <ClauseSelector seleccionadas={clausulas} onChange={setClausulas} nuevas={clausulasNuevas} onNuevasChange={setClausulasNuevas} />
      <button className="btn" type="submit">Generar contrato de venta</button>
      {msg.err && <span className="error-text">{msg.err}</span>}
      {msg.ok && <span style={{ color: 'var(--color-success)' }}>{msg.ok}</span>}
    </form>
  )
}

// Vista dedicada para el detalle y la administración de una solicitud.
export default function RequestDetail() {
  const { id } = useParams()
  const [sol, setSol] = useState(null)
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const { users, props, propLabel } = useLookups(sol ? [sol.usuario_id] : [], sol ? [sol.inmueble_id] : [])

  async function cargar() {
    setLoading(true)
    try { setSol(await rentalsApi.get(id)) }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cargar la solicitud.' }) }
    finally { setLoading(false) }
  }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { cargar() }, [id])

  async function cambiarEstado(estado) {
    if (estado === sol.estado) return
    const tipo = sol.tipo_operacion === 'venta' ? 'compra' : 'renta'
    // Confirmación reforzada al aprobar (acción importante del proceso).
    const aviso = estado === 'aprobada'
      ? `¿Aprobar esta solicitud de ${tipo}? Luego podrás generar el contrato correspondiente.`
      : `¿Cambiar el estado de la solicitud a "${capitalizar(estado)}"?`
    if (!window.confirm(aviso)) { cargar(); return }
    setMsg({ ok: '', err: '' })
    try { await rentalsApi.setEstado(sol.id, estado); cargar() }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo actualizar la solicitud.' }) }
  }

  if (loading) return <Spinner label="Cargando solicitud…" />
  if (!sol) return <Alert type="error">{msg.err || 'Solicitud no encontrada.'}</Alert>

  const cliente = users[sol.usuario_id]
  const inm = props[sol.inmueble_id]

  return (
    <div className="stack">
      <p><Link to="/admin/solicitudes">← Volver a solicitudes</Link></p>
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h1>{folioSolicitud(sol.id)} — {sol.tipo_operacion === 'venta' ? 'Compra' : 'Renta'}</h1>
        <span className="badge">{capitalizar(sol.estado)}</span>
      </div>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      <div className="grid form-2">
        <div className="card" style={{ background: '#faf8ff' }}>
          <h4 style={{ margin: '0 0 .3rem' }}>Cliente</h4>
          <p className="muted" style={{ margin: 0 }}>
            {cliente ? <>{cliente.nombre}<br />{cliente.correo}<br />Tel: {cliente.telefono || '—'}</> : `Cliente #${sol.usuario_id}`}
          </p>
        </div>
        <div className="card" style={{ background: '#faf8ff' }}>
          <h4 style={{ margin: '0 0 .3rem' }}>Inmueble</h4>
          <p className="muted" style={{ margin: 0 }}>
            <Link to={`/inmueble/${sol.inmueble_id}`}>{propLabel(sol.inmueble_id)}</Link>
            {inm && <><br />{capitalizar(tipoDe(inm))} · {capitalizar(usoDe(inm))}<br /><strong>Precio publicado: {formatoMoneda(inm.precio)}</strong></>}
          </p>
        </div>
      </div>

      <p className="muted" style={{ margin: 0 }}>
        <strong>Fechas solicitadas:</strong> {sol.fecha_inicio || '—'} → {sol.fecha_fin || '—'}
        {sol.duracion_meses ? ` · ${sol.duracion_meses} mes(es)` : ''}
        {sol.mensaje ? ` · Nota: "${sol.mensaje}"` : ''}
      </p>

      <div className="card">
        <label htmlFor="est">Estado de la solicitud</label>
        <select id="est" value={sol.estado} onChange={(e) => cambiarEstado(e.target.value)}>
          {ESTADOS.map((e) => <option key={e} value={e}>{capitalizar(e)}</option>)}
        </select>
      </div>

      {sol.estado === 'aprobada' && !sol.contrato_id && (
        <div className="card">
          {sol.tipo_operacion === 'venta'
            ? <GenerarContratoVenta solicitud={sol} precioPublicado={inm?.precio} onDone={cargar} />
            : <GenerarContrato solicitud={sol} precioPublicado={inm?.precio} onDone={cargar} />}
        </div>
      )}
      {sol.contrato_id && (
        <p className="muted">Contrato generado: <Link to={`/admin/contratos/${sol.contrato_id}`}>abrir contrato #{sol.contrato_id}</Link></p>
      )}
    </div>
  )
}
