// Geocodificación con Nominatim (OpenStreetMap). Sin API key.
// Nota: uso ligero (política de uso de OSM); apto para este proyecto.
const BASE = 'https://nominatim.openstreetmap.org'

// Mapea la respuesta de Nominatim a los campos de Ubicacion de Propify.
function mapAddress(item) {
  const a = item.address || {}
  return {
    latitud: Number(item.lat),
    longitud: Number(item.lon),
    direccion_completa: item.display_name || '',
    calle: a.road || a.pedestrian || a.footway || '',
    numero_exterior: a.house_number || '',
    colonia: a.neighbourhood || a.suburb || a.quarter || a.residential || '',
    ciudad: a.city || a.town || a.village || a.municipality || a.county || '',
    estado: a.state || '',
    codigo_postal: a.postcode || '',
  }
}

// Coordenadas -> dirección
export async function reverseGeocode(lat, lng) {
  const url = `${BASE}/reverse?format=jsonv2&lat=${lat}&lon=${lng}&accept-language=es&addressdetails=1`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) throw new Error('reverse geocode failed')
  const data = await res.json()
  return mapAddress(data)
}

// Texto -> lista de resultados
export async function searchAddress(query) {
  const url = `${BASE}/search?format=jsonv2&q=${encodeURIComponent(query)}&accept-language=es&addressdetails=1&limit=5`
  const res = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!res.ok) throw new Error('search failed')
  const data = await res.json()
  return data.map((item) => ({ label: item.display_name, ...mapAddress(item) }))
}
