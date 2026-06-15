import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { contractsApi } from '../../api/contracts'
import { formatoMoneda, capitalizar } from '../../utils/constants'
import { useLookups } from '../../hooks/useLookups'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import DataTable from '../../components/DataTable'
import Spinner from '../../components/Spinner'

const ESTADOS = ['borrador', 'pendiente_de_firma', 'firmado', 'activo', 'finalizado', 'cancelado', 'liquidado']
const etiqueta = (e) => capitalizar((e || '').replace(/_/g, ' '))
const nuevoInit = { fecha_inicio: '', fecha_fin: '', tipo: 'Venta', monto: '', usuario_id: '', inmueble_id: '', url_archivo: '' }

export default function ContractsAdmin() {
  const [filtros, setFiltros] = useState({ estado: '', tipo: '', usuario_id: '', inmueble_id: '', fecha_desde: '', fecha_hasta: '' })
  const [contratos, setContratos] = useState([])
  const [loading, setLoading] = useState(true)
  const [nuevo, setNuevo] = useState(nuevoInit)
  const [msg, setMsg] = useState({ ok: '', err: '' })

  const { userLabel, propLabel } = useLookups(
    contratos.map((c) => c.usuario_id), contratos.map((c) => c.inmueble_id),
  )

  async function cargar() {
    setLoading(true)
    try {
      const params = Object.fromEntries(Object.entries(filtros).filter(([, v]) => v !== ''))
      setContratos(await contractsApi.listAll(params))
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar los contratos.' })
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const setF = (f) => (e) => setFiltros((s) => ({ ...s, [f]: e.target.value }))
  const setN = (f) => (e) => setNuevo((s) => ({ ...s, [f]: e.target.value }))

  async function crear(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    try {
      await contractsApi.create({
        fecha_inicio: nuevo.fecha_inicio, fecha_fin: nuevo.fecha_fin || null, tipo: nuevo.tipo,
        monto: Number(nuevo.monto), usuario_id: Number(nuevo.usuario_id), inmueble_id: Number(nuevo.inmueble_id),
        url_archivo: nuevo.url_archivo || null,
      })
      setMsg({ ok: 'Contrato generado.', err: '' }); setNuevo(nuevoInit); cargar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo generar el contrato.' }) }
  }

  const columns = [
    { key: 'folio', header: 'Folio', render: (r) => r.folio || `#${r.id}` },
    { key: 'cliente', header: 'Cliente', render: (r) => userLabel(r.usuario_id) },
    { key: 'inmueble', header: 'Inmueble', render: (r) => propLabel(r.inmueble_id) },
    { key: 'tipo', header: 'Operación' },
    { key: 'monto', header: 'Monto', render: (r) => formatoMoneda(r.monto) },
    { key: 'estado', header: 'Estado', render: (r) => <span className="badge">{etiqueta(r.estado)}</span> },
    { key: 'vigencia', header: 'Vigencia', render: (r) => `${r.fecha_inicio}${r.fecha_fin ? ' → ' + r.fecha_fin : ''}` },
    { key: 'acc', header: '', render: (r) => (
        <Link className="btn small secondary" to={`/admin/contratos/${r.id}`}>Abrir</Link>) },
  ]

  return (
    <div className="stack">
      <h1>Gestión de contratos</h1>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      {/* Filtros */}
      <form className="card" onSubmit={(e) => { e.preventDefault(); cargar() }} aria-label="Filtros de contratos">
        <div className="grid form-2">
          <Field label="Estado" as="select" options={ESTADOS.map((e) => ({ value: e, label: etiqueta(e) }))} value={filtros.estado} onChange={setF('estado')} />
          <Field label="Operación" as="select" options={['Venta', 'Renta']} value={filtros.tipo} onChange={setF('tipo')} />
          <Field label="ID cliente" type="number" value={filtros.usuario_id} onChange={setF('usuario_id')} />
          <Field label="ID inmueble" type="number" value={filtros.inmueble_id} onChange={setF('inmueble_id')} />
          <Field label="Desde" type="date" value={filtros.fecha_desde} onChange={setF('fecha_desde')} />
          <Field label="Hasta" type="date" value={filtros.fecha_hasta} onChange={setF('fecha_hasta')} />
        </div>
        <div className="row">
          <button className="btn" type="submit">Aplicar filtros</button>
          <button className="btn secondary" type="button" onClick={() => { setFiltros({ estado: '', tipo: '', usuario_id: '', inmueble_id: '', fecha_desde: '', fecha_hasta: '' }); setTimeout(cargar, 0) }}>Limpiar</button>
        </div>
      </form>

      {loading ? <Spinner /> : (
        <DataTable caption={`${contratos.length} contrato(s)`} columns={columns} rows={contratos} empty="No hay contratos." />
      )}

      {/* Generar contrato manual */}
      <details className="card">
        <summary style={{ fontWeight: 600 }}>Generar contrato manualmente</summary>
        <form onSubmit={crear} noValidate style={{ marginTop: '1rem' }}>
          <div className="grid form-2">
            <Field label="Tipo de contrato" as="select" options={['Venta', 'Renta']} value={nuevo.tipo} onChange={setN('tipo')} required />
            <Field label="Monto (MXN)" type="number" min="0" value={nuevo.monto} onChange={setN('monto')} required />
            <Field label="Fecha inicio" type="date" value={nuevo.fecha_inicio} onChange={setN('fecha_inicio')} required />
            <Field label="Fecha fin" type="date" value={nuevo.fecha_fin} onChange={setN('fecha_fin')} hint="Requerida para renta." />
            <Field label="ID cliente" type="number" value={nuevo.usuario_id} onChange={setN('usuario_id')} required />
            <Field label="ID inmueble" type="number" value={nuevo.inmueble_id} onChange={setN('inmueble_id')} required />
          </div>
          <button className="btn" type="submit">Generar contrato</button>
        </form>
      </details>
    </div>
  )
}
