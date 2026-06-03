import { Link } from 'react-router-dom'
import { capitalizar, formatoMoneda } from '../utils/constants'

export default function PropertyCard({ inmueble, imagen }) {
  const estado = (inmueble.estado || '').toLowerCase()
  return (
    <article className="card property-card stack">
      {imagen ? (
        <img src={imagen.url_archivo} alt={imagen.texto_alternativo || inmueble.titulo} />
      ) : (
        <img src="" alt={`Sin fotografía disponible de ${inmueble.titulo}`} />
      )}
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <span className="price">{formatoMoneda(inmueble.precio)}</span>
        <span className={`badge ${estado}`}>{capitalizar(estado)}</span>
      </div>
      <h3 style={{ margin: 0 }}>{inmueble.titulo}</h3>
      <p className="muted" style={{ margin: 0 }}>
        {capitalizar(inmueble.tipo)} · {capitalizar(inmueble.operacion)} · {capitalizar(inmueble.uso)}
      </p>
      <p className="muted" style={{ margin: 0 }}>
        {inmueble.num_recamaras ?? 0} rec · {inmueble.num_banos ?? 0} baños
        {inmueble.area_construccion ? ` · ${inmueble.area_construccion} m²` : ''}
      </p>
      <Link className="btn" to={`/inmueble/${inmueble.id}`}>
        Ver detalle<span className="sr-only"> de {inmueble.titulo}</span>
      </Link>
    </article>
  )
}
