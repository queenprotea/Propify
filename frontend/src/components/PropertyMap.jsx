import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { Link } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import '../utils/leaflet'

// Mapa interactivo con alternativa textual accesible (WCAG 1.1.1).
// points: [{ id, titulo, lat, lng, direccion }]
export default function PropertyMap({ points = [], center = [19.4326, -99.1332] }) {
  const valid = points.filter((p) => p.lat != null && p.lng != null)
  const mapCenter = valid.length ? [Number(valid[0].lat), Number(valid[0].lng)] : center

  return (
    <section aria-label="Mapa de inmuebles">
      <div role="application" aria-label="Mapa interactivo con la ubicación de los inmuebles">
        <MapContainer center={mapCenter} zoom={11} scrollWheelZoom={false}>
          <TileLayer
            attribution='&copy; colaboradores de OpenStreetMap'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          {valid.map((p) => (
            <Marker key={p.id} position={[Number(p.lat), Number(p.lng)]}>
              <Popup>
                <strong>{p.titulo}</strong>
                <br />
                {p.direccion}
                <br />
                <Link to={`/inmueble/${p.id}`}>Ver detalle</Link>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Alternativa textual al mapa para lectores de pantalla y sin JS visual */}
      <details>
        <summary>Ver lista de ubicaciones (alternativa al mapa)</summary>
        {valid.length === 0 ? (
          <p className="muted">No hay ubicaciones con coordenadas para mostrar.</p>
        ) : (
          <ul>
            {valid.map((p) => (
              <li key={p.id}>
                <Link to={`/inmueble/${p.id}`}>{p.titulo}</Link> — {p.direccion}
              </li>
            ))}
          </ul>
        )}
      </details>
    </section>
  )
}
