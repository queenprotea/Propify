import { useEffect, useState } from 'react'
import { contractsApi } from '../../api/contracts'
import { formatoMoneda } from '../../utils/constants'
import { useLookups } from '../../hooks/useLookups'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import DataTable from '../../components/DataTable'
import ContractPanel from '../../components/ContractPanel'
import Spinner from '../../components/Spinner'

const TABS = [
  { key: 'activo', label: 'Activas' },
  { key: 'finalizado', label: 'Finalizadas' },
  { key: 'cancelado', label: 'Canceladas' },
]

function Renovar({ contrato, onDone }) {
  const [f, setF] = useState({ fecha_inicio: '', fecha_fin: '', monto: contrato.monto })
  const [msg, setMsg] = useState('')
  async function go(e) {
    e.preventDefault()
    try { await contractsApi.renovar(contrato.id, { ...f, monto: Number(f.monto) }); onDone() }
    catch (err) { setMsg(err.response?.data?.detail || 'No se pudo renovar.') }
  }
  return (
    <form onSubmit={go} className="toolbar" aria-label={`Renovar contrato ${contrato.id}`}>
      <Field label="Nuevo inicio" type="date" value={f.fecha_inicio} onChange={(e) => setF((s) => ({ ...s, fecha_inicio: e.target.value }))} required />
      <Field label="Nuevo fin" type="date" value={f.fecha_fin} onChange={(e) => setF((s) => ({ ...s, fecha_fin: e.target.value }))} required />
      <Field label="Renta mensual" type="number" min="0" value={f.monto} onChange={(e) => setF((s) => ({ ...s, monto: e.target.value }))} required />
      <button className="btn small" type="submit">Renovar</button>
      {msg && <span className="error-text">{msg}</span>}
    </form>
  )
}

export default function RentsAdmin() {
  const [tab, setTab] = useState('activo')
  const [rentas, setRentas] = useState([])
  const [loading, setLoading] = useState(true)
  const [seleccionado, setSeleccionado] = useState(null)
  const [renovando, setRenovando] = useState(null)
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const manualInit = { usuario_id: '', inmueble_id: '', fecha_inicio: '', fecha_fin: '', monto: '', condiciones: '', estado: 'activo' }
  const [manual, setManual] = useState(manualInit)
  const setM = (f) => (e) => setManual((s) => ({ ...s, [f]: e.target.value }))

  async function registrarManual(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    try {
      await contractsApi.rentaManual({
        usuario_id: Number(manual.usuario_id), inmueble_id: Number(manual.inmueble_id),
        fecha_inicio: manual.fecha_inicio, fecha_fin: manual.fecha_fin,
        monto: Number(manual.monto), condiciones: manual.condiciones || null, estado: manual.estado,
      })
      setManual(manualInit); setMsg({ ok: 'Renta registrada; contrato y calendario generados, inmueble rentado.', err: '' })
      setTab('activo'); cargar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo registrar la renta.' }) }
  }

  const { userLabel, propLabel } = useLookups(rentas.map((r) => r.usuario_id), rentas.map((r) => r.inmueble_id))

  async function cargar() {
    setLoading(true)
    try { setRentas(await contractsApi.listAll({ tipo: 'Renta', estado: tab })) }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar las rentas.' }) }
    finally { setLoading(false) }
  }
  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  async function finalizar(id) {
    if (!window.confirm('¿Finalizar esta renta? El inmueble quedará disponible.')) return
    setMsg({ ok: '', err: '' })
    try { await contractsApi.finalizar(id); setMsg({ ok: 'Renta finalizada; inmueble liberado.', err: '' }); cargar() }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo finalizar.' }) }
  }
  async function cancelar(id) {
    if (!window.confirm('¿Cancelar esta renta? El inmueble quedará disponible.')) return
    setMsg({ ok: '', err: '' })
    try { await contractsApi.cancelar(id); setMsg({ ok: 'Renta cancelada; inmueble liberado.', err: '' }); cargar() }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cancelar.' }) }
  }

  const columns = [
    { key: 'folio', header: 'Folio', render: (r) => r.folio || `#${r.id}` },
    { key: 'cliente', header: 'Cliente', render: (r) => userLabel(r.usuario_id) },
    { key: 'inmueble', header: 'Inmueble', render: (r) => propLabel(r.inmueble_id) },
    { key: 'inicio', header: 'Inicio', render: (r) => r.fecha_inicio },
    { key: 'fin', header: 'Vencimiento', render: (r) => r.fecha_fin || '—' },
    { key: 'monto', header: 'Renta', render: (r) => formatoMoneda(r.monto) },
    { key: 'acc', header: 'Acciones', render: (r) => (
      <div className="row">
        <button className="btn small secondary" type="button" onClick={() => setSeleccionado(seleccionado === r.id ? null : r.id)}>Detalle</button>
        {tab === 'activo' && <>
          <button className="btn small secondary" type="button" onClick={() => setRenovando(renovando === r.id ? null : r.id)}>Renovar</button>
          <button className="btn small" type="button" onClick={() => finalizar(r.id)}>Finalizar</button>
          <button className="btn small danger" type="button" onClick={() => cancelar(r.id)}>Cancelar</button>
        </>}
      </div>) },
  ]

  const sel = rentas.find((r) => r.id === seleccionado)
  const ren = rentas.find((r) => r.id === renovando)

  return (
    <div className="stack">
      <h1>Gestión de rentas</h1>
      <div className="alert info">
        <strong>Finalizar</strong>: la renta concluyó normalmente y cumplió el periodo acordado — se registra como
        operación <strong>completada</strong> y se conserva todo el historial de pagos.<br />
        <strong>Cancelar</strong>: la renta se anuló o no llegó a completarse (revocación o decisión de alguna parte) —
        <strong>no</strong> cuenta como completada. En ambos casos el inmueble vuelve a estar disponible y se conserva el historial.
      </div>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      <details className="card">
        <summary style={{ fontWeight: 600 }}>Registrar renta manual</summary>
        <p className="muted">El administrador registra directamente una renta. Se generan automáticamente el contrato, el calendario de pagos y se actualiza el inmueble a «rentado».</p>
        <form onSubmit={registrarManual} className="stack">
          <div className="grid form-2">
            <Field label="ID cliente" type="number" value={manual.usuario_id} onChange={setM('usuario_id')} required />
            <Field label="ID inmueble" type="number" value={manual.inmueble_id} onChange={setM('inmueble_id')} required />
            <Field label="Fecha de inicio" type="date" value={manual.fecha_inicio} onChange={setM('fecha_inicio')} required />
            <Field label="Fecha de finalización" type="date" value={manual.fecha_fin} onChange={setM('fecha_fin')} required />
            <Field label="Precio mensual (MXN)" type="number" min="0" value={manual.monto} onChange={setM('monto')} required />
            <Field label="Estado de la renta" as="select"
                   options={['activo', 'borrador', 'pendiente_de_firma', 'firmado'].map((e) => ({ value: e, label: e.replace(/_/g, ' ') }))}
                   value={manual.estado} onChange={setM('estado')} />
          </div>
          <Field label="Condiciones especiales" as="textarea" value={manual.condiciones} onChange={setM('condiciones')} />
          <button className="btn" type="submit">Registrar renta</button>
        </form>
      </details>

      <div className="op-tabs" role="tablist" aria-label="Estado de las rentas" style={{ background: '#efe9fb' }}>
        {TABS.map((t) => (
          <button key={t.key} type="button" role="tab" aria-selected={tab === t.key}
                  aria-pressed={tab === t.key} onClick={() => { setTab(t.key); setSeleccionado(null); setRenovando(null) }}
                  style={tab === t.key ? { background: '#fff', color: 'var(--color-primary-dark)' } : { color: 'var(--color-primary-dark)' }}>
            {t.label}
          </button>
        ))}
      </div>

      {loading ? <Spinner /> : (
        <DataTable caption={`Rentas ${TABS.find((t) => t.key === tab).label.toLowerCase()}`} columns={columns} rows={rentas} empty="No hay rentas en este estado." />
      )}

      {ren && (
        <div className="card stack">
          <h3 style={{ margin: 0 }}>Renovar {ren.folio || `#${ren.id}`}</h3>
          <Renovar contrato={ren} onDone={() => { setRenovando(null); setMsg({ ok: 'Contrato renovado.', err: '' }); cargar() }} />
        </div>
      )}

      {sel && <ContractPanel contrato={sel} admin />}
    </div>
  )
}
