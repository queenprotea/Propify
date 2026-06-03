import { useEffect, useState } from 'react'
import { auditApi } from '../../api/contracts'
import DataTable from '../../components/DataTable'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function AuditAdmin() {
  const [registros, setRegistros] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filtro, setFiltro] = useState('')

  useEffect(() => {
    let activo = true
    auditApi.list()
      .then((r) => { if (activo) setRegistros(r || []) })
      .catch((err) => { if (activo) setError(err.response?.data?.detail || 'No se pudo cargar la auditoría.') })
      .finally(() => { if (activo) setLoading(false) })
    return () => { activo = false }
  }, [])

  const filtrados = registros.filter((r) =>
    !filtro || r.accion?.toLowerCase().includes(filtro.toLowerCase()) || (r.entidad || '').toLowerCase().includes(filtro.toLowerCase()))

  const columns = [
    { key: 'fecha', header: 'Fecha y hora', render: (r) => new Date(r.fecha).toLocaleString('es-MX') },
    { key: 'usuario_id', header: 'Usuario', render: (r) => (r.usuario_id ? `#${r.usuario_id}` : 'sistema') },
    { key: 'accion', header: 'Acción' },
    { key: 'entidad', header: 'Entidad', render: (r) => `${r.entidad || ''}${r.entidad_id ? ' #' + r.entidad_id : ''}` },
    { key: 'valor_anterior', header: 'Valor anterior', render: (r) => r.valor_anterior || '—' },
    { key: 'valor_nuevo', header: 'Valor nuevo', render: (r) => r.valor_nuevo || '—' },
    { key: 'detalle', header: 'Detalle', render: (r) => r.detalle || '—' },
  ]

  if (loading) return <Spinner label="Cargando auditoría…" />

  return (
    <div className="stack">
      <h1>Auditoría del sistema</h1>
      <p className="muted">Bitácora de acciones críticas (inmuebles, contratos, solicitudes, pagos y usuarios) para reconstruir cualquier operación.</p>
      {error && <Alert type="error">{error}</Alert>}
      <div style={{ maxWidth: 360 }}>
        <Field label="Filtrar por acción o entidad" value={filtro} onChange={(e) => setFiltro(e.target.value)} />
      </div>
      <DataTable caption={`${filtrados.length} registro(s)`} columns={columns} rows={filtrados} empty="Sin registros de auditoría." />
    </div>
  )
}
