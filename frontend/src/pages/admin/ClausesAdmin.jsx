import { useEffect, useState } from 'react'
import { clausesApi } from '../../api/contracts'
import Field from '../../components/Field'
import Alert from '../../components/Alert'
import Spinner from '../../components/Spinner'

const nuevoInit = { numero: '', titulo: '', texto: '' }

// Indentación visual según el nivel jerárquico del número (2, 2.1, 2.1.1).
const nivel = (numero) => (numero || '').split('.').length - 1

export default function ClausesAdmin() {
  const [clausulas, setClausulas] = useState([])
  const [nuevo, setNuevo] = useState(nuevoInit)
  const [loading, setLoading] = useState(true)
  const [msg, setMsg] = useState({ ok: '', err: '' })

  async function cargar() {
    setLoading(true)
    try { setClausulas(await clausesApi.list()) }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo cargar el catálogo.' }) }
    finally { setLoading(false) }
  }
  useEffect(() => { cargar() }, [])

  const setN = (f) => (e) => setNuevo((s) => ({ ...s, [f]: e.target.value }))

  async function crear(e) {
    e.preventDefault()
    setMsg({ ok: '', err: '' })
    if (!/^\d+(\.\d+)*$/.test(nuevo.numero.trim())) {
      setMsg({ ok: '', err: 'El número debe ser jerárquico: dígitos separados por puntos (2, 2.1, 2.1.1).' }); return
    }
    try {
      await clausesApi.create({ numero: nuevo.numero.trim(), titulo: nuevo.titulo.trim(), texto: nuevo.texto.trim() })
      setNuevo(nuevoInit); setMsg({ ok: 'Cláusula agregada al catálogo.', err: '' }); cargar()
    } catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo crear la cláusula.' }) }
  }

  async function eliminar(id) {
    if (!window.confirm('¿Eliminar esta cláusula del catálogo?')) return
    setMsg({ ok: '', err: '' })
    try { await clausesApi.remove(id); setMsg({ ok: 'Cláusula eliminada.', err: '' }); cargar() }
    catch (err) { setMsg({ ok: '', err: err.response?.data?.detail || 'No se pudo eliminar.' }) }
  }

  return (
    <div className="stack">
      <h1>Catálogo de cláusulas</h1>
      <p className="muted">
        Define cláusulas reutilizables con numeración jerárquica (por ejemplo 2, 2.1, 2.1.1).
        Al generar un contrato podrás seleccionarlas para incluirlas.
      </p>
      <Alert type="error">{msg.err}</Alert>
      <Alert type="success">{msg.ok}</Alert>

      <form className="card" onSubmit={crear} noValidate>
        <div className="grid form-2">
          <Field label="Número" value={nuevo.numero} onChange={setN('numero')} required placeholder="2.1.1" maxLength={20} />
          <Field label="Título" value={nuevo.titulo} onChange={setN('titulo')} required maxLength={200} />
        </div>
        <Field label="Texto de la cláusula" as="textarea" value={nuevo.texto} onChange={setN('texto')} required maxLength={2000} />
        <button className="btn" type="submit">Agregar cláusula</button>
      </form>

      {loading ? <Spinner /> : (
        <div className="card stack">
          <h2 style={{ margin: 0 }}>Cláusulas ({clausulas.length})</h2>
          {clausulas.length === 0 ? (
            <p className="muted">Aún no hay cláusulas en el catálogo.</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {clausulas.map((c) => (
                <li key={c.id} className="row" style={{ justifyContent: 'space-between', alignItems: 'start',
                  paddingLeft: `${nivel(c.numero) * 1.5}rem`, borderTop: '1px solid var(--color-border)', paddingTop: 8, paddingBottom: 8 }}>
                  <span><strong>{c.numero} {c.titulo}</strong><br /><span className="muted">{c.texto}</span></span>
                  <button className="btn small danger" type="button" onClick={() => eliminar(c.id)}>Eliminar</button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  )
}
