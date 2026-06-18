// Taxonomía del inmueble (catálogos normalizados por id en el backend).
export const ESTADOS_INMUEBLE = ['en venta', 'vendido', 'en renta', 'rentado', 'reservado', 'no disponible']
export const ESTADOS_PUBLICOS = ['en venta', 'en renta', 'reservado']
export const USOS = ['residencial', 'comercial']

const TIPOS_COMERCIALES = [
  'local comercial', 'bodega comercial', 'local de centro comercial', 'oficina',
  'terreno comercial', 'terreno industrial', 'edificio',
]

export const estadoDe = (inm) => inm?.estado_inmueble?.valor || ''
export const tipoDe = (inm) => inm?.tipo_inmueble?.valor || ''
export const usoDe = (inm) => (TIPOS_COMERCIALES.includes(tipoDe(inm)) ? 'comercial' : 'residencial')

export function operacionDe(inm) {
  const e = estadoDe(inm)
  if (e === 'en venta' || e === 'vendido') return 'venta'
  if (e === 'en renta' || e === 'rentado') return 'renta'
  return ''
}

export const claseEstado = (valor) => (valor || '').replace(/ /g, '-')

export const ESTADOS_REPUBLICA = [
  'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas',
  'Chihuahua', 'Ciudad de Mexico', 'Coahuila', 'Colima', 'Durango', 'Estado de Mexico',
  'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacan', 'Morelos', 'Nayarit',
  'Nuevo Leon', 'Oaxaca', 'Puebla', 'Queretaro', 'Quintana Roo', 'San Luis Potosi',
  'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatan', 'Zacatecas',
]

export const METODOS_PAGO = ['stripe', 'transferencia', 'efectivo']

// Folio legible de una solicitud (el cliente puede dárselo al admin para localizarla).
export function folioSolicitud(id) {
  return `SOL-${String(id).padStart(5, '0')}`
}

// Nombre: solo letras (con acentos y ñ), espacios y los signos . ' - (consistente con el backend).
export const NOMBRE_RE = /^[A-Za-zÁÉÍÓÚÜáéíóúüÑñ]+(?:[ .'-][A-Za-zÁÉÍÓÚÜáéíóúüÑñ]+)*$/

export function validarNombre(v) {
  const n = (v || '').trim().replace(/\s+/g, ' ')
  if (n.length < 2) return 'El nombre es obligatorio (mínimo 2 caracteres).'
  if (n.length > 100) return 'El nombre no debe exceder 100 caracteres.'
  if (/\d/.test(n)) return 'El nombre no puede contener números.'
  if (!NOMBRE_RE.test(n)) return "El nombre solo admite letras, espacios y los signos . ' -"
  return ''
}

// Texto libre: rechaza caracteres inválidos y secuencias de símbolos sin sentido
// (consistente con el backend). Devuelve '' si es válido, o el mensaje de error.
const _CARS_INVALIDOS = /[<>{}[\]\\|^~`]/
const _SIMBOLOS_SPAM = /[¿?¡!*#]{2,}/

export function validarTexto(v, campo = 'El texto') {
  const s = v || ''
  if (_CARS_INVALIDOS.test(s)) return `${campo} contiene caracteres no permitidos (< > { } [ ] \\ | ^ ~ \`).`
  if (_SIMBOLOS_SPAM.test(s)) return `${campo} contiene una secuencia de símbolos no válida.`
  return ''
}

export function capitalizar(s) {
  if (!s) return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
}

export function formatoMoneda(n) {
  const num = Number(n)
  if (Number.isNaN(num)) return '—'
  return num.toLocaleString('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 })
}
