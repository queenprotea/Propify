import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { propertiesApi, historyApi } from '../../api/properties'
import { ESTADOS, capitalizar, formatoMoneda } from '../../utils/constants'
import DataTable from '../../components/DataTable'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function PropertiesAdmin() {
  const [inmuebles, setInmuebles] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })

  async function cargar() {
    setLoading(true)
    try {
      setInmuebles(await propertiesApi.list(100, 0))
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar los inmuebles.' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { cargar() }, [])

  async function eliminar(inm) {
    if (!window.confirm(`¿Eliminar el inmueble "${inm.titulo}"? Esta acción no se puede deshacer.`)) return
    setMsg({ ok: '', err: '' })
    try {
      await propertiesApi.remove(inm.id)
      setMsg({ ok: `Inmueble "${inm.titulo}" eliminado.`, err: '' })
      cargar()
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo eliminar el inmueble.' })
    }
  }

  async function cambiarEstado(inm, nuevoEstado) {
    setMsg({ ok: '', err: '' })
    try {
      // Registrar en historial actualiza también el estado actual del inmueble.
      await historyApi.create({ inmueble_id: inm.id, estado: nuevoEstado })
      setMsg({ ok: `Estado de "${inm.titulo}" actualizado a ${nuevoEstado}.`, err: '' })
      cargar()
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cambiar el estado.' })
    }
  }

  const columns = [
    { key: 'titulo', header: 'Título', render: (r) => <Link to={`/inmueble/${r.id}`}>{r.titulo}</Link> },
    { key: 'tipo', header: 'Tipo', render: (r) => capitalizar(r.tipo) },
    { key: 'operacion', header: 'Operación', render: (r) => capitalizar(r.operacion) },
    { key: 'precio', header: 'Precio', render: (r) => formatoMoneda(r.precio) },
    { key: 'estado', header: 'Estado', render: (r) => <span className={`badge ${(r.estado || '').toLowerCase()}`}>{capitalizar(r.estado)}</span> },
    {
      key: 'acciones', header: 'Acciones',
      render: (r) => (
        <div className="row">
          <Link className="btn small secondary" to={`/admin/inmuebles/${r.id}/editar`}>Editar</Link>
          <label className="sr-only" htmlFor={`estado-${r.id}`}>Cambiar estado de {r.titulo}</label>
          <select
            id={`estado-${r.id}`}
            value={r.estado}
            onChange={(e) => cambiarEstado(r, e.target.value)}
          >
            {ESTADOS.map((s) => <option key={s} value={s}>{capitalizar(s)}</option>)}
          </select>
          <button className="btn small danger" type="button" onClick={() => eliminar(r)}>
            Eliminar<span className="sr-only"> {r.titulo}</span>
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="stack">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h1>Gestión de inmuebles</h1>
        <Link className="btn" to="/admin/inmuebles/nuevo">Publicar inmueble</Link>
      </div>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>
      {loading ? <Spinner /> : (
        <DataTable caption="Inmuebles publicados" columns={columns} rows={inmuebles} empty="No hay inmuebles." />
      )}
    </div>
  )
}
