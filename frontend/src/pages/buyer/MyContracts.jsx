import { useEffect, useState } from 'react'
import { contractsApi } from '../../api/contracts'
import { useAuth } from '../../context/AuthContext'
import ContractPanel from '../../components/ContractPanel'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function MyContracts() {
  const { user } = useAuth()
  const [contratos, setContratos] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let activo = true
    contractsApi.byUser(user.id)
      .then((c) => { if (activo) setContratos(c || []) })
      .catch((err) => { if (activo) setError(err.response?.data?.detail || 'No se pudieron cargar tus contratos.') })
      .finally(() => { if (activo) setLoading(false) })
    return () => { activo = false }
  }, [user.id])

  if (loading) return <Spinner label="Cargando contratos…" />

  return (
    <div className="stack">
      <h1>Mis contratos</h1>
      {error && <Alert type="error">{error}</Alert>}
      {contratos.length === 0 ? (
        <p className="muted">No tienes contratos asociados a tu cuenta.</p>
      ) : (
        contratos.map((c) => <ContractPanel key={c.id} contrato={c} />)
      )}
    </div>
  )
}
