import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { contractsApi } from '../../api/contracts'
import { useAuth } from '../../context/AuthContext'
import { formatoMoneda, capitalizar } from '../../utils/constants'
import { useLookups } from '../../hooks/useLookups'
import DataTable from '../../components/DataTable'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

const etiqueta = (e) => capitalizar((e || '').replace(/_/g, ' '))

// Listado compacto: solo lo relevante. El detalle completo está en /mis-contratos/:id.
export default function MyContracts() {
  const { user } = useAuth()
  const [contratos, setContratos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { propLabel } = useLookups([], contratos.map((c) => c.inmueble_id))

  useEffect(() => {
    let activo = true
    contractsApi.byUser(user.id)
      .then((c) => { if (activo) setContratos(c || []) })
      .catch((err) => { if (activo) setError(err.response?.data?.detail || 'No se pudieron cargar tus contratos.') })
      .finally(() => { if (activo) setLoading(false) })
    return () => { activo = false }
  }, [user.id])

  if (loading) return <Spinner label="Cargando contratos…" />

  const columns = [
    { key: 'folio', header: 'Folio', render: (r) => <strong>{r.folio || `#${r.id}`}</strong> },
    { key: 'tipo', header: 'Operación', render: (r) => r.tipo },
    { key: 'inmueble', header: 'Inmueble', render: (r) => propLabel(r.inmueble_id) },
    { key: 'monto', header: 'Monto', render: (r) => formatoMoneda(r.monto) },
    { key: 'estado', header: 'Estado', render: (r) => <span className="badge">{etiqueta(r.estado)}</span> },
    { key: 'acc', header: '', render: (r) => <Link className="btn small secondary" to={`/mis-contratos/${r.id}`}>Ver detalle</Link> },
  ]

  return (
    <div className="stack">
      <h1>Mis contratos</h1>
      {error && <Alert type="error">{error}</Alert>}
      {contratos.length === 0 ? (
        <p className="muted">No tienes contratos asociados a tu cuenta.</p>
      ) : (
        <DataTable caption={`${contratos.length} contrato(s)`} columns={columns} rows={contratos} empty="No tienes contratos." />
      )}
    </div>
  )
}
