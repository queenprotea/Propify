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
const filtrosInit = { folio: '', estado: '', tipo: '', fecha_desde: '', fecha_hasta: '' }

// Los contratos se generan desde solicitudes aprobadas; aquí solo se consultan y abren.
export default function ContractsAdmin() {
  const [filtros, setFiltros] = useState(filtrosInit)
  const [contratos, setContratos] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })

  const { propLabel } = useLookups([], contratos.map((c) => c.inmueble_id))

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

  // Búsqueda principal por folio (identificador natural de la operación diaria).
  const columns = [
    { key: 'folio', header: 'Folio', render: (r) => <strong>{r.folio || `#${r.id}`}</strong> },
    { key: 'tipo', header: 'Operación', render: (r) => r.tipo },
    { key: 'inmueble', header: 'Inmueble', render: (r) => propLabel(r.inmueble_id) },
    { key: 'monto', header: 'Monto', render: (r) => formatoMoneda(r.monto) },
    { key: 'estado', header: 'Estado', render: (r) => <span className="badge">{etiqueta(r.estado)}</span> },
    { key: 'acc', header: '', render: (r) => <Link className="btn small secondary" to={`/admin/contratos/${r.id}`}>Abrir</Link> },
  ]

  return (
    <div className="stack">
      <h1>Contratos</h1>
      <Alert type="error">{msg.err}</Alert>

      {/* Búsqueda por folio + filtros (sin depender del cliente). */}
      <form className="card stack" onSubmit={(e) => { e.preventDefault(); cargar() }} aria-label="Buscar contratos">
        <Field label="Buscar por folio" value={filtros.folio} onChange={setF('folio')} placeholder="Ej. CTR-2026-00007" maxLength={30} />
        <div className="grid form-2">
          <Field label="Operación" as="select" options={['Venta', 'Renta']} value={filtros.tipo} onChange={setF('tipo')} />
          <Field label="Estado" as="select" options={ESTADOS.map((e) => ({ value: e, label: etiqueta(e) }))} value={filtros.estado} onChange={setF('estado')} />
          <Field label="Desde" type="date" value={filtros.fecha_desde} onChange={setF('fecha_desde')} />
          <Field label="Hasta" type="date" value={filtros.fecha_hasta} onChange={setF('fecha_hasta')} />
        </div>
        <div className="row">
          <button className="btn" type="submit">Buscar</button>
          <button className="btn secondary" type="button" onClick={() => { setFiltros(filtrosInit); setTimeout(cargar, 0) }}>Limpiar</button>
        </div>
      </form>

      {loading ? <Spinner /> : (
        <DataTable caption={`${contratos.length} contrato(s)`} columns={columns} rows={contratos} empty="No hay contratos que coincidan." />
      )}
    </div>
  )
}
