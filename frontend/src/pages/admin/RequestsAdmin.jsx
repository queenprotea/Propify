import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { rentalsApi } from '../../api/contracts'
import { capitalizar, folioSolicitud } from '../../utils/constants'
import { useLookups } from '../../hooks/useLookups'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import DataTable from '../../components/DataTable'
import Spinner from '../../components/Spinner'

// Listado ligero de solicitudes; el detalle y la gestión están en la vista dedicada.
export default function RequestsAdmin() {
  const [solicitudes, setSolicitudes] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const [busqueda, setBusqueda] = useState('')
  const { userLabel, propLabel } = useLookups(
    solicitudes.map((s) => s.usuario_id), solicitudes.map((s) => s.inmueble_id),
  )

  async function cargar() {
    setLoading(true)
    try { setSolicitudes(await rentalsApi.all()) }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar las solicitudes.' }) }
    finally { setLoading(false) }
  }
  useEffect(() => { cargar() }, [])

  if (loading) return <Spinner />

  // Filtro por folio/ID (el cliente proporciona el folio para localizar su trámite).
  const q = busqueda.trim().toLowerCase()
  const filtradas = q
    ? solicitudes.filter((s) => folioSolicitud(s.id).toLowerCase().includes(q) || String(s.id) === q.replace(/^sol-/, '').replace(/^0+/, ''))
    : solicitudes

  const columns = [
    { key: 'id', header: 'Folio', render: (r) => <strong>{folioSolicitud(r.id)}</strong> },
    { key: 'tipo_operacion', header: 'Tipo', render: (r) => (r.tipo_operacion === 'venta' ? 'Compra' : 'Renta') },
    { key: 'cliente', header: 'Cliente', render: (r) => userLabel(r.usuario_id) },
    { key: 'inmueble', header: 'Inmueble', render: (r) => propLabel(r.inmueble_id) },
    { key: 'estado', header: 'Estado', render: (r) => <span className="badge">{capitalizar(r.estado)}</span> },
    { key: 'acc', header: '', render: (r) => <Link className="btn small secondary" to={`/admin/solicitudes/${r.id}`}>Abrir</Link> },
  ]

  return (
    <div className="stack">
      <h1>Solicitudes de renta y compra</h1>
      <Alert type="error">{msg.err}</Alert>

      <div className="card">
        <Field label="Buscar por folio o ID" value={busqueda} onChange={(e) => setBusqueda(e.target.value)}
               placeholder="Ej. SOL-00007 o 7" />
      </div>

      <DataTable caption={`${filtradas.length} solicitud(es)`} columns={columns} rows={filtradas} empty="No hay solicitudes." />
    </div>
  )
}
