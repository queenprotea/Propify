import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { visitsApi } from '../../api/users'
import { useLookups } from '../../hooks/useLookups'
import DataTable from '../../components/DataTable'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function VisitsAdmin() {
  const [visitas, setVisitas] = useState([])
  const [estados, setEstados] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })
  const { userLabel, propLabel } = useLookups(visitas.map((v) => v.usuario_id), visitas.map((v) => v.inmueble_id))

  async function cargar() {
    setLoading(true)
    try {
      const [v, e] = await Promise.all([visitsApi.all(), visitsApi.states()])
      setVisitas(v || []); setEstados(e || [])
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar las visitas.' })
    } finally {
      setLoading(false)
    }
  }
  useEffect(() => { cargar() }, [])

  async function cambiarEstado(visita, estadoId) {
    setMsg({ ok: '', err: '' })
    try {
      await visitsApi.update(visita.id, { estado_id: Number(estadoId) })
      setMsg({ ok: 'Visita actualizada.', err: '' })
      cargar()
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo actualizar la visita.' })
    }
  }

  const columns = [
    { key: 'id', header: '#' },
    { key: 'fecha', header: 'Fecha', render: (r) => new Date(r.fecha).toLocaleString('es-MX') },
    { key: 'inmueble_id', header: 'Inmueble', render: (r) => <Link to={`/inmueble/${r.inmueble_id}`}>{propLabel(r.inmueble_id)}</Link> },
    { key: 'usuario_id', header: 'Cliente', render: (r) => userLabel(r.usuario_id) },
    {
      key: 'estado', header: 'Estado',
      render: (r) => (
        <>
          <label className="sr-only" htmlFor={`v-${r.id}`}>Estado de la visita #{r.id}</label>
          <select id={`v-${r.id}`} value={r.estado_id} onChange={(e) => cambiarEstado(r, e.target.value)}>
            {estados.map((s) => <option key={s.id} value={s.id}>{s.valor}</option>)}
          </select>
        </>
      ),
    },
  ]

  if (loading) return <Spinner />

  return (
    <div className="stack">
      <h1>Agenda de visitas</h1>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>
      <DataTable caption="Visitas programadas" columns={columns} rows={visitas} empty="No hay visitas." />
    </div>
  )
}
