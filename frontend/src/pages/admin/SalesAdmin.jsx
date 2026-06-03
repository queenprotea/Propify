import { useEffect, useState } from 'react'
import { contractsApi } from '../../api/contracts'
import { formatoMoneda, capitalizar } from '../../utils/constants'
import { useLookups } from '../../hooks/useLookups'
import DataTable from '../../components/DataTable'
import Alert from '../../components/Alert'
import ContractPanel from '../../components/ContractPanel'
import Spinner from '../../components/Spinner'

const TABS = [
  { key: 'activo', label: 'En proceso' },
  { key: 'liquidado', label: 'Liquidadas' },
  { key: 'cancelado', label: 'Canceladas' },
]
const etiqueta = (e) => capitalizar((e || '').replace(/_/g, ' '))

export default function SalesAdmin() {
  const [tab, setTab] = useState('activo')
  const [ventas, setVentas] = useState([])
  const [loading, setLoading] = useState(true)
  const [seleccionado, setSeleccionado] = useState(null)
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const { userLabel, propLabel } = useLookups(ventas.map((v) => v.usuario_id), ventas.map((v) => v.inmueble_id))

  async function cargar() {
    setLoading(true)
    try { setVentas(await contractsApi.listAll({ tipo: 'Venta', estado: tab })) }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar las ventas.' }) }
    finally { setLoading(false) }
  }
  useEffect(() => {
    cargar()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab])

  const columns = [
    { key: 'folio', header: 'Folio', render: (r) => r.folio || `#${r.id}` },
    { key: 'cliente', header: 'Comprador', render: (r) => userLabel(r.usuario_id) },
    { key: 'inmueble', header: 'Inmueble', render: (r) => propLabel(r.inmueble_id) },
    { key: 'monto', header: 'Precio', render: (r) => formatoMoneda(r.monto) },
    { key: 'estado', header: 'Estado', render: (r) => <span className="badge">{etiqueta(r.estado)}</span> },
    { key: 'acc', header: '', render: (r) => (
        <button className="btn small secondary" type="button" onClick={() => setSeleccionado(seleccionado === r.id ? null : r.id)}>
          {seleccionado === r.id ? 'Cerrar' : 'Detalle'}
        </button>) },
  ]
  const sel = ventas.find((v) => v.id === seleccionado)

  return (
    <div className="stack">
      <h1>Gestión de ventas</h1>
      <p className="muted">Operaciones de compraventa. El inmueble pasa a «reservado» al formalizar y a «vendido» al liquidar el precio total.</p>
      <Alert type="error">{msg.err}</Alert>

      <div className="op-tabs" role="tablist" aria-label="Estado de las ventas" style={{ background: '#efe9fb' }}>
        {TABS.map((t) => (
          <button key={t.key} type="button" role="tab" aria-selected={tab === t.key} aria-pressed={tab === t.key}
                  onClick={() => { setTab(t.key); setSeleccionado(null) }}
                  style={tab === t.key ? { background: '#fff', color: 'var(--color-primary-dark)' } : { color: 'var(--color-primary-dark)' }}>
            {t.label}
          </button>
        ))}
      </div>

      {loading ? <Spinner /> : (
        <DataTable caption={`Ventas ${TABS.find((t) => t.key === tab).label.toLowerCase()}`} columns={columns} rows={ventas} empty="No hay ventas en este estado." />
      )}

      {sel && <ContractPanel contrato={sel} admin />}
    </div>
  )
}
