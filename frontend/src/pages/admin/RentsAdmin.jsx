import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { contractsApi } from '../../api/contracts'
import { formatoMoneda } from '../../utils/constants'
import { useLookups } from '../../hooks/useLookups'
import Alert from '../../components/Alert'
import DataTable from '../../components/DataTable'
import Spinner from '../../components/Spinner'

const TABS = [
  { key: 'activo', label: 'Activas' },
  { key: 'finalizado', label: 'Finalizadas' },
  { key: 'cancelado', label: 'Canceladas' },
]

// Las rentas se originan desde solicitudes aprobadas del cliente. Aquí solo se
// consultan y se cierran (finalizar/cancelar); el detalle vive en la vista de contrato.
export default function RentsAdmin() {
  const [tab, setTab] = useState('activo')
  const [rentas, setRentas] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })

  const { propLabel } = useLookups([], rentas.map((r) => r.inmueble_id))

  async function cargar() {
    setLoading(true)
    try { setRentas(await contractsApi.listAll({ tipo: 'Renta', estado: tab })) }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar las rentas.' }) }
    finally { setLoading(false) }
  }
  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  async function finalizar(id) {
    if (!window.confirm('¿Finalizar esta renta? Se registrará como completada.')) return
    setMsg({ ok: '', err: '' })
    try { await contractsApi.finalizar(id); setMsg({ ok: 'Renta finalizada.', err: '' }); cargar() }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo finalizar.' }) }
  }
  async function cancelar(id) {
    if (!window.confirm('¿Cancelar esta renta?')) return
    setMsg({ ok: '', err: '' })
    try { await contractsApi.cancelar(id); setMsg({ ok: 'Renta cancelada.', err: '' }); cargar() }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cancelar.' }) }
  }

  const columns = [
    { key: 'folio', header: 'Folio', render: (r) => <strong>{r.folio || `#${r.id}`}</strong> },
    { key: 'inmueble', header: 'Inmueble', render: (r) => propLabel(r.inmueble_id) },
    { key: 'inicio', header: 'Inicio', render: (r) => r.fecha_inicio },
    { key: 'fin', header: 'Vencimiento', render: (r) => r.fecha_fin || '—' },
    { key: 'monto', header: 'Renta', render: (r) => formatoMoneda(r.monto) },
    { key: 'acc', header: 'Acciones', render: (r) => (
      <div className="row">
        <Link className="btn small secondary" to={`/admin/contratos/${r.id}`}>Detalle</Link>
        {tab === 'activo' && <>
          <button className="btn small" type="button" onClick={() => finalizar(r.id)}>Finalizar</button>
          <button className="btn small danger" type="button" onClick={() => cancelar(r.id)}>Cancelar</button>
        </>}
      </div>) },
  ]

  return (
    <div className="stack">
      <h1>Gestión de rentas</h1>
      <div className="alert info">
        <strong>Finalizar</strong>: la renta concluyó normalmente (se registra como completada).<br />
        <strong>Cancelar</strong>: la renta se anuló o no llegó a completarse. En ambos casos se conserva el historial;
        la disponibilidad del inmueble se ajusta manualmente desde Inmuebles.
      </div>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      <div className="op-tabs" role="tablist" aria-label="Estado de las rentas" style={{ background: '#efe9fb' }}>
        {TABS.map((t) => (
          <button key={t.key} type="button" role="tab" aria-selected={tab === t.key}
                  aria-pressed={tab === t.key} onClick={() => setTab(t.key)}
                  style={tab === t.key ? { background: '#fff', color: 'var(--color-primary-dark)' } : { color: 'var(--color-primary-dark)' }}>
            {t.label}
          </button>
        ))}
      </div>

      {loading ? <Spinner /> : (
        <DataTable caption={`Rentas ${TABS.find((t) => t.key === tab).label.toLowerCase()}`} columns={columns} rows={rentas} empty="No hay rentas en este estado." />
      )}
    </div>
  )
}
