import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { contactsApi } from '../../api/properties'
import { useLookups } from '../../hooks/useLookups'
import DataTable from '../../components/DataTable'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function ContactsAdmin() {
  const [contactos, setContactos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { propLabel } = useLookups([], contactos.map((c) => c.inmueble_id))

  useEffect(() => {
    let activo = true
    contactsApi.all(200, 0)
      .then((c) => { if (activo) setContactos(c || []) })
      .catch((err) => { if (activo) setError(err.response?.data?.detail || 'No se pudieron cargar los contactos.') })
      .finally(() => { if (activo) setLoading(false) })
    return () => { activo = false }
  }, [])

  const columns = [
    { key: 'fecha', header: 'Fecha', render: (r) => new Date(r.fecha).toLocaleString('es-MX') },
    { key: 'nombre', header: 'Nombre' },
    { key: 'correo', header: 'Correo' },
    { key: 'inmueble_id', header: 'Inmueble', render: (r) => <Link to={`/inmueble/${r.inmueble_id}`}>{propLabel(r.inmueble_id)}</Link> },
    { key: 'mensaje', header: 'Mensaje' },
  ]

  if (loading) return <Spinner />

  return (
    <div className="stack">
      <h1>Reporte de contactos</h1>
      <p className="muted">Seguimiento comercial de los interesados que enviaron mensajes.</p>
      {error && <Alert type="error">{error}</Alert>}
      <DataTable caption="Contactos recibidos" columns={columns} rows={contactos} empty="No hay contactos registrados." />
    </div>
  )
}
