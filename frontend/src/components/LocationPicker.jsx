import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import '../utils/leaflet'
import { reverseGeocode, searchAddress } from '../utils/geocode'

const DEFAULT_CENTER = [19.4326, -99.1332] // Ciudad de México

function ClickHandler({ onPick }) {
  useMapEvents({ click(e) { onPick(e.latlng.lat, e.latlng.lng) } })
  return null
}

function Recenter({ position }) {
  const map = useMap()
  useEffect(() => {
    if (position) map.setView(position, Math.max(map.getZoom(), 15))
  }, [position, map])
  return null
}

// Selector de ubicación en mapa. Llama onPick(info) con lat/lng + dirección.
export default function LocationPicker({ value, onPick }) {
  const inicial = value?.latitud && value?.longitud ? [Number(value.latitud), Number(value.longitud)] : null
  const [pos, setPos] = useState(inicial)
  const [q, setQ] = useState('')
  const [resultados, setResultados] = useState([])
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState('')

  async function aplicar(lat, lng, datos = null) {
    setPos([lat, lng])
    setMsg('Obteniendo dirección…')
    try {
      const info = datos || (await reverseGeocode(lat, lng))
      onPick({ ...info, latitud: lat, longitud: lng })
      setMsg('Ubicación seleccionada.')
    } catch {
      onPick({ latitud: lat, longitud: lng })
      setMsg('Se guardaron las coordenadas (no se pudo obtener la dirección).')
    }
  }

  async function buscar(e) {
    e.preventDefault()
    if (!q.trim()) return
    setBusy(true); setMsg(''); setResultados([])
    try {
      const r = await searchAddress(q.trim())
      setResultados(r)
      if (r.length === 0) setMsg('Sin resultados para esa búsqueda.')
    } catch {
      setMsg('No se pudo buscar la dirección.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="stack">
      <p className="muted" style={{ margin: 0 }}>
        Busca una dirección, haz clic en el mapa o arrastra el marcador para fijar la ubicación.
      </p>

      <form onSubmit={buscar} className="row" aria-label="Buscar dirección en el mapa">
        <div className="field" style={{ marginBottom: 0, flex: 1, minWidth: 220 }}>
          <label htmlFor="map-search">Buscar dirección</label>
          <input id="map-search" type="text" value={q} onChange={(e) => setQ(e.target.value)}
                 placeholder="Ej. Av. Reforma 222, CDMX" />
        </div>
        <button className="btn small" type="submit" disabled={busy}>{busy ? 'Buscando…' : 'Buscar'}</button>
      </form>

      {resultados.length > 0 && (
        <ul style={{ listStyle: 'none', border: '1px solid var(--color-border)', borderRadius: 'var(--radius)' }}>
          {resultados.map((r, i) => (
            <li key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
              <button type="button" className="nav-btn" style={{ width: '100%', textAlign: 'left' }}
                      onClick={() => { aplicar(r.latitud, r.longitud, r); setResultados([]); setQ(r.label) }}>
                {r.label}
              </button>
            </li>
          ))}
        </ul>
      )}

      <div role="application" aria-label="Mapa para seleccionar la ubicación del inmueble">
        <MapContainer center={pos || DEFAULT_CENTER} zoom={pos ? 15 : 11} style={{ height: 360 }}>
          <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          <ClickHandler onPick={aplicar} />
          <Recenter position={pos} />
          {pos && (
            <Marker
              position={pos}
              draggable
              eventHandlers={{
                dragend(e) { const ll = e.target.getLatLng(); aplicar(ll.lat, ll.lng) },
              }}
            />
          )}
        </MapContainer>
      </div>

      {pos && (
        <p className="muted" aria-live="polite" style={{ margin: 0 }}>
          {msg} Coordenadas: {pos[0].toFixed(5)}, {pos[1].toFixed(5)}
        </p>
      )}
    </div>
  )
}
