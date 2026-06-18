import { useEffect, useState } from 'react'
import { clausesApi } from '../api/contracts'
import Field from './Field'

const nivel = (numero) => (numero || '').split('.').length - 1
const nuevaInit = { numero: '', titulo: '', texto: '' }

// Selector de cláusulas: permite marcar las del catálogo (seleccionadas/onChange)
// y además escribir cláusulas nuevas al momento (nuevas/onNuevasChange).
export default function ClauseSelector({ seleccionadas, onChange, nuevas, onNuevasChange }) {
  const [clausulas, setClausulas] = useState([])
  const [error, setError] = useState('')
  const [borrador, setBorrador] = useState(nuevaInit)

  useEffect(() => {
    clausesApi.list().then(setClausulas).catch(() => setError('No se pudo cargar el catálogo de cláusulas.'))
  }, [])

  function toggle(id) {
    const set = new Set(seleccionadas)
    set.has(id) ? set.delete(id) : set.add(id)
    onChange([...set])
  }

  function agregarNueva() {
    if (!/^\d+(\.\d+)*$/.test(borrador.numero.trim()) || !borrador.titulo.trim() || !borrador.texto.trim()) {
      setError('Para agregar una cláusula nueva: número jerárquico (2.1), título y texto.')
      return
    }
    setError('')
    onNuevasChange([...(nuevas || []), {
      numero: borrador.numero.trim(), titulo: borrador.titulo.trim(), texto: borrador.texto.trim(),
    }])
    setBorrador(nuevaInit)
  }

  function quitarNueva(i) {
    onNuevasChange((nuevas || []).filter((_, idx) => idx !== i))
  }

  return (
    <fieldset className="card" style={{ background: '#fbfbff' }}>
      <legend style={{ fontWeight: 500 }}>Cláusulas del contrato</legend>
      {error && <p className="muted" style={{ color: 'var(--color-danger)' }}>{error}</p>}

      {/* Del catálogo */}
      {clausulas.length === 0 ? (
        <p className="muted">No hay cláusulas en el catálogo. Puedes agregarlas abajo o en «Cláusulas».</p>
      ) : (
        clausulas.map((c) => (
          <label key={c.id} className="row" style={{ alignItems: 'start', gap: 8, paddingLeft: `${nivel(c.numero) * 1.2}rem`, marginBottom: 4 }}>
            <input type="checkbox" checked={seleccionadas.includes(c.id)} onChange={() => toggle(c.id)} style={{ width: 'auto', marginTop: 4 }} />
            <span><strong>{c.numero} {c.titulo}</strong> <span className="muted">— {c.texto}</span></span>
          </label>
        ))
      )}

      {/* Nuevas (ad-hoc) ya agregadas */}
      {(nuevas || []).length > 0 && (
        <ul style={{ marginTop: 8 }}>
          {nuevas.map((n, i) => (
            <li key={i} className="row" style={{ justifyContent: 'space-between' }}>
              <span><strong>{n.numero} {n.titulo}</strong> <span className="muted">— {n.texto}</span></span>
              <button className="btn small danger" type="button" onClick={() => quitarNueva(i)}>Quitar</button>
            </li>
          ))}
        </ul>
      )}

      {/* Agregar una cláusula nueva al momento */}
      <details style={{ marginTop: 8 }}>
        <summary style={{ cursor: 'pointer' }}>Agregar una cláusula nueva</summary>
        <div className="grid form-2" style={{ marginTop: 8 }}>
          <Field label="Número" value={borrador.numero} onChange={(e) => setBorrador((s) => ({ ...s, numero: e.target.value }))} placeholder="2.1" maxLength={20} />
          <Field label="Título" value={borrador.titulo} onChange={(e) => setBorrador((s) => ({ ...s, titulo: e.target.value }))} maxLength={200} />
        </div>
        <Field label="Texto" as="textarea" value={borrador.texto} onChange={(e) => setBorrador((s) => ({ ...s, texto: e.target.value }))} maxLength={2000} />
        <button className="btn small" type="button" onClick={agregarNueva}>Agregar cláusula</button>
      </details>
    </fieldset>
  )
}
