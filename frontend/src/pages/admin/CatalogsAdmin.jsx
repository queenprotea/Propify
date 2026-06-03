import { useEffect, useState } from 'react'
import { propertiesApi } from '../../api/properties'
import { capitalizar } from '../../utils/constants'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

const CATALOGOS = [
  { key: 'tipos', label: 'Tipos de inmueble', editable: true },
  { key: 'usos', label: 'Usos del inmueble', editable: true },
  { key: 'operaciones', label: 'Tipos de operación', editable: false },
  { key: 'estados', label: 'Estados del inmueble', editable: false },
]

export default function CatalogsAdmin() {
  const [cat, setCat] = useState(null)
  const [nuevos, setNuevos] = useState({})
  const [msg, setMsg] = useState({ ok: '', err: '' })

  async function cargar() {
    try { setCat(await propertiesApi.categorias()) }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudieron cargar los catálogos.' }) }
  }
  useEffect(() => { cargar() }, [])

  async function agregar(key) {
    const valor = (nuevos[key] || '').trim()
    if (!valor) return
    setMsg({ ok: '', err: '' })
    try {
      await propertiesApi.addCategoria(key, valor)
      setNuevos((n) => ({ ...n, [key]: '' }))
      setMsg({ ok: `Valor "${valor}" agregado.`, err: '' })
      cargar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo agregar.' }) }
  }
  async function eliminar(key, valor) {
    if (!window.confirm(`¿Eliminar "${valor}" del catálogo?`)) return
    setMsg({ ok: '', err: '' })
    try {
      await propertiesApi.deleteCategoria(key, valor)
      setMsg({ ok: `Valor "${valor}" eliminado.`, err: '' })
      cargar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo eliminar.' }) }
  }

  if (!cat) return <Spinner label="Cargando catálogos…" />

  return (
    <div className="stack">
      <h1>Catálogos de inmuebles</h1>
      <p className="muted">Administra los valores de tipo y uso (escalables). Operación y estado son fijos porque
        determinan los flujos de negocio (renta/venta, disponible/reservado/vendido/rentado).</p>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      <div className="grid cards">
        {CATALOGOS.map(({ key, label, editable }) => (
          <section key={key} className="card stack" aria-label={label}>
            <h2 style={{ margin: 0 }}>{label}</h2>
            <ul>
              {(cat[key] || []).map((v) => (
                <li key={v} className="row" style={{ justifyContent: 'space-between' }}>
                  <span>{capitalizar(v)}</span>
                  {editable && (
                    <button className="btn small danger" type="button" onClick={() => eliminar(key, v)}>
                      Eliminar<span className="sr-only"> {v}</span>
                    </button>
                  )}
                </li>
              ))}
            </ul>
            {editable && (
              <form className="row" onSubmit={(e) => { e.preventDefault(); agregar(key) }}>
                <label className="sr-only" htmlFor={`add-${key}`}>Nuevo valor para {label}</label>
                <input id={`add-${key}`} type="text" placeholder="Nuevo valor"
                       value={nuevos[key] || ''} onChange={(e) => setNuevos((n) => ({ ...n, [key]: e.target.value }))}
                       style={{ flex: 1, minWidth: 120 }} />
                <button className="btn small" type="submit">Agregar</button>
              </form>
            )}
          </section>
        ))}
      </div>
    </div>
  )
}
