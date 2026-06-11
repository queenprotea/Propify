import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { propertiesApi } from '../../api/properties'
import { capitalizar, formatoMoneda, estadoDe, tipoDe, operacionDe, claseEstado } from '../../utils/constants'
import { useCategorias } from '../../hooks/useCategorias'
import DataTable from '../../components/DataTable'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

export default function PropertiesAdmin() {
  const cat = useCategorias()
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
    if (!window.confirm(`¿Eliminar el inmueble "${inm.titulo}"? Pasará a 'no disponible' y dejará de mostrarse al público (eliminación lógica).`)) return
    setMsg({ ok: '', err: '' })
    try {
      await propertiesApi.remove(inm.id)
      setMsg({ ok: `Inmueble "${inm.titulo}" marcado como no disponible.`, err: '' })
      cargar()
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo eliminar el inmueble.' })
    }
  }

  async function cambiarEstado(inm, estadoId) {
    setMsg({ ok: '', err: '' })
    try {
      const r = await propertiesApi.updateStatus(inm.id, Number(estadoId))
      setMsg({ ok: `Estado de "${inm.titulo}" actualizado a ${estadoDe(r) || 'nuevo estado'}.`, err: '' })
      cargar()
    } catch (err) {
      setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cambiar el estado.' })
    }
  }

  const columns = [
    { key: 'titulo', header: 'Título', render: (r) => <Link to={`/inmueble/${r.id}`}>{r.titulo}</Link> },
    { key: 'tipo', header: 'Tipo', render: (r) => capitalizar(tipoDe(r)) },
    { key: 'operacion', header: 'Operación', render: (r) => capitalizar(operacionDe(r)) || '—' },
    { key: 'precio', header: 'Precio', render: (r) => formatoMoneda(r.precio) },
    { key: 'estado', header: 'Estado', render: (r) => <span className={`badge ${claseEstado(estadoDe(r))}`}>{capitalizar(estadoDe(r))}</span> },
    {
      key: 'acciones', header: 'Acciones',
      render: (r) => (
        <div className="row">
          <Link className="btn small secondary" to={`/admin/inmuebles/${r.id}/editar`}>Editar</Link>
          <label className="sr-only" htmlFor={`estado-${r.id}`}>Cambiar estado de {r.titulo}</label>
          <select
            id={`estado-${r.id}`}
            value={r.estado_id}
            onChange={(e) => cambiarEstado(r, e.target.value)}
          >
            {cat.estados.map((s) => <option key={s.id} value={s.id}>{capitalizar(s.valor)}</option>)}
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
