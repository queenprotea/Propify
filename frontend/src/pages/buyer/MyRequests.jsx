import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { rentalsApi } from '../../api/contracts'
import { useAuth } from '../../context/AuthContext'
import { capitalizar } from '../../utils/constants'
import DataTable from '../../components/DataTable'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function MyRequests() {
  const { user } = useAuth()
  const [solicitudes, setSolicitudes] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })

  async function cargar() {
    setLoading(true)
    try { setSolicitudes(await rentalsApi.byUser(user.id)) }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar tus solicitudes.' }) }
    finally { setLoading(false) }
  }
  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user.id])

  async function cancelar(id) {
    setMsg({ ok: '', err: '' })
    try { await rentalsApi.cancel(id); setMsg({ ok: 'Solicitud cancelada.', err: '' }); cargar() }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cancelar.' }) }
  }

  const columns = [
    { key: 'id', header: '#' },
    { key: 'inmueble_id', header: 'Inmueble', render: (r) => <Link to={`/inmueble/${r.inmueble_id}`}>#{r.inmueble_id}</Link> },
    { key: 'fecha_solicitud', header: 'Fecha', render: (r) => new Date(r.fecha_solicitud).toLocaleDateString('es-MX') },
    { key: 'estado', header: 'Estado', render: (r) => capitalizar(r.estado) },
    { key: 'contrato_id', header: 'Contrato', render: (r) => r.contrato_id
        ? <Link to="/mis-contratos">Ver contrato</Link> : '—' },
    {
      key: 'acciones', header: 'Acciones',
      render: (r) => (['pendiente', 'en revision'].includes(r.estado)
        ? <button className="btn small danger" type="button" onClick={() => cancelar(r.id)}>Cancelar</button>
        : <span className="muted">—</span>),
    },
  ]

  if (loading) return <Spinner label="Cargando solicitudes…" />

  return (
    <div className="stack">
      <h1>Mis solicitudes de renta</h1>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>
      <DataTable caption="Solicitudes" columns={columns} rows={solicitudes} empty="No has realizado solicitudes de renta." />
    </div>
  )
}
