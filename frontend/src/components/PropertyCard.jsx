import { Link } from 'react-router-dom'
import { capitalizar, formatoMoneda, estadoDe, tipoDe, usoDe, claseEstado } from '../utils/constants'

export default function PropertyCard({ inmueble, imagen }) {
  const estado = estadoDe(inmueble)
  const foto = imagen || inmueble.imagenes?.[0]
  return (
    <article className="card property-card stack">
      {foto ? (
        <img src={foto.url_archivo} alt={foto.descripcion || inmueble.titulo} />
      ) : (
        <img src="" alt={`Sin fotografía disponible de ${inmueble.titulo}`} />
      )}
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <span className="price">{formatoMoneda(inmueble.precio)}</span>
        <span className={`badge ${claseEstado(estado)}`}>{capitalizar(estado)}</span>
      </div>
      <h3 style={{ margin: 0 }}>{inmueble.titulo}</h3>
      <p className="muted" style={{ margin: 0 }}>
        {capitalizar(tipoDe(inmueble))} · {capitalizar(usoDe(inmueble))}
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
