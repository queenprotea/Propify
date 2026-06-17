import { Link } from 'react-router-dom'
import { capitalizar, formatoMoneda, estadoDe, tipoDe, usoDe, claseEstado } from '../utils/constants'

export default function PropertyCard({ inmueble, imagen }) {
  const estado = estadoDe(inmueble)
  const foto = imagen || inmueble.imagenes?.[0]
  const ubi = inmueble.ubicacion
  const ubicacionTexto = [ubi?.colonia, ubi?.ciudad, ubi?.estado_republica?.valor]
    .filter(Boolean).join(', ')

  return (
    <article className="property-card">
      <div className="prop-img-wrap">
        {foto ? (
          <img src={foto.url_archivo} alt={foto.descripcion || inmueble.titulo} loading="lazy" />
        ) : (
          <div className="prop-no-photo" aria-label={`Sin fotografía disponible de ${inmueble.titulo}`}>
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.4" aria-hidden="true">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <circle cx="8.5" cy="8.5" r="1.5"/>
              <path d="M21 15l-5-5L5 21"/>
            </svg>
          </div>
        )}
        <span className={`badge ${claseEstado(estado)}`}>{capitalizar(estado)}</span>
      </div>

      <div className="prop-body">
        <div className="prop-price">{formatoMoneda(inmueble.precio)}</div>
        <h3 className="prop-title">{inmueble.titulo}</h3>
        <p className="prop-type">
          {capitalizar(tipoDe(inmueble))} · {capitalizar(usoDe(inmueble))}
        </p>
        {ubicacionTexto && (
          <p className="prop-location">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true" style={{ flexShrink: 0 }}>
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
              <circle cx="12" cy="10" r="3"/>
            </svg>
            {ubicacionTexto}
          </p>
        )}

        <div className="prop-features">
          {inmueble.num_recamaras != null && (
            <span className="prop-feat">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M2 20v-8a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v8"/>
                <path d="M4 10V6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v4"/>
                <path d="M12 4v6"/>
                <path d="M2 18h20"/>
              </svg>
              {inmueble.num_recamaras} rec.
            </span>
          )}
          {inmueble.num_banos != null && (
            <span className="prop-feat">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <path d="M9 6L9 2a1 1 0 0 0-1-1H4a1 1 0 0 0-1 1v14"/>
                <path d="M3 10h18a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H3a0 0 0 0 1 0 0V10z"/>
                <path d="M5 18v2 M19 18v2"/>
              </svg>
              {inmueble.num_banos} {inmueble.num_banos === 1 ? 'baño' : 'baños'}
            </span>
          )}
          {inmueble.area_construccion && (
            <span className="prop-feat">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                <rect x="3" y="3" width="18" height="18" rx="1"/>
                <path d="M3 9h18 M9 21V9"/>
              </svg>
              {inmueble.area_construccion} m²
            </span>
          )}
        </div>

        <Link className="btn full" to={`/inmueble/${inmueble.id}`}>
          Ver detalles<span className="sr-only"> de {inmueble.titulo}</span>
        </Link>
      </div>
    </article>
  )
}
