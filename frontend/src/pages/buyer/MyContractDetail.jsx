import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { contractsApi } from '../../api/contracts'
import ContractPanel from '../../components/ContractPanel'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

// Detalle completo de un contrato del cliente (pagos, firmado, comprobantes).
export default function MyContractDetail() {
  const { id } = useParams()
  const [contrato, setContrato] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let activo = true
    contractsApi.get(id)
      .then((c) => { if (activo) setContrato(c) })
      .catch((err) => { if (activo) setError(err.response?.data?.detail || 'No se pudo cargar el contrato.') })
      .finally(() => { if (activo) setLoading(false) })
    return () => { activo = false }
  }, [id])

  return (
    <div className="stack">
      <p><Link to="/mis-contratos">← Volver a mis contratos</Link></p>
      <h1>Contrato {contrato?.folio || `#${id}`}</h1>
      {error && <Alert type="error">{error}</Alert>}
      {loading ? <Spinner label="Cargando contrato…" /> : (contrato && <ContractPanel contrato={contrato} />)}
    </div>
  )
}
