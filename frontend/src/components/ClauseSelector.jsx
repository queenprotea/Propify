import { useEffect, useState } from 'react'
import { clausesApi } from '../api/contracts'

const nivel = (numero) => (numero || '').split('.').length - 1

// Selector de cláusulas del catálogo para incluir en un contrato.
// Notifica al padre los ids marcados mediante onChange.
export default function ClauseSelector({ seleccionadas, onChange }) {
  const [clausulas, setClausulas] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    clausesApi.list()
      .then(setClausulas)
      .catch(() => setError('No se pudo cargar el catálogo de cláusulas.'))
  }, [])

  function toggle(id) {
    const set = new Set(seleccionadas)
    set.has(id) ? set.delete(id) : set.add(id)
    onChange([...set])
  }

  if (error) return <p className="muted">{error}</p>
  if (clausulas.length === 0) return <p className="muted">No hay cláusulas en el catálogo. Agrégalas en «Cláusulas».</p>

  return (
    <fieldset className="card" style={{ background: '#fbfbff' }}>
      <legend style={{ fontWeight: 500 }}>Cláusulas a incluir</legend>
      {clausulas.map((c) => (
        <label key={c.id} className="row" style={{ alignItems: 'start', gap: 8, paddingLeft: `${nivel(c.numero) * 1.2}rem`, marginBottom: 4 }}>
          <input type="checkbox" checked={seleccionadas.includes(c.id)} onChange={() => toggle(c.id)} style={{ width: 'auto', marginTop: 4 }} />
          <span><strong>{c.numero} {c.titulo}</strong> <span className="muted">— {c.texto}</span></span>
        </label>
      ))}
    </fieldset>
  )
}
