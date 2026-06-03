import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { visitsApi } from '../../api/users'
import { useAuth } from '../../context/AuthContext'
import DataTable from '../../components/DataTable'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function MyVisits() {
  const { user } = useAuth()
  const [visitas, setVisitas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let activo = true
    visitsApi.byUser(user.id)
      .then((v) => { if (activo) setVisitas(v || []) })
      .catch((err) => { if (activo) setError(err.response?.data?.detail || 'No se pudieron cargar tus visitas.') })
      .finally(() => { if (activo) setLoading(false) })
    return () => { activo = false }
  }, [user.id])

  const columns = [
    { key: 'inmueble_id', header: 'Inmueble', render: (r) => <Link to={`/inmueble/${r.inmueble_id}`}>#{r.inmueble_id}</Link> },
    { key: 'fecha', header: 'Fecha', render: (r) => new Date(r.fecha).toLocaleString('es-MX') },
    { key: 'estado', header: 'Estado', render: (r) => r.estado?.valor || `#${r.estado_id}` },
  ]

  if (loading) return <Spinner label="Cargando visitas…" />

  return (
    <div className="stack">
      <h1>Mis visitas</h1>
      {error && <Alert type="error">{error}</Alert>}
      <DataTable caption="Visitas agendadas" columns={columns} rows={visitas} empty="Aún no tienes visitas agendadas." />
    </div>
  )
}
