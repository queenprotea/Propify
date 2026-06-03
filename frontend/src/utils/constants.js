// Catálogos de la taxonomía del inmueble (coinciden con los enums del backend).
export const TIPOS = ['casa', 'departamento', 'terreno', 'local', 'edificio', 'oficina']
export const OPERACIONES = ['venta', 'renta']
export const USOS = ['residencial', 'comercial', 'industrial', 'mixto', 'terreno']
export const ESTADOS = ['disponible', 'reservado', 'vendido', 'rentado']

export const ESTADOS_REPUBLICA = [
  'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Chiapas',
  'Chihuahua', 'Ciudad de Mexico', 'Coahuila', 'Colima', 'Durango', 'Estado de Mexico',
  'Guanajuato', 'Guerrero', 'Hidalgo', 'Jalisco', 'Michoacan', 'Morelos', 'Nayarit',
  'Nuevo Leon', 'Oaxaca', 'Puebla', 'Queretaro', 'Quintana Roo', 'San Luis Potosi',
  'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatan', 'Zacatecas',
]

export const METODOS_PAGO = ['stripe', 'transferencia', 'efectivo']

export function capitalizar(s) {
  if (!s) return ''
  return s.charAt(0).toUpperCase() + s.slice(1)
}

export function formatoMoneda(n) {
  const num = Number(n)
  if (Number.isNaN(num)) return '—'
  return num.toLocaleString('es-MX', { style: 'currency', currency: 'MXN', maximumFractionDigits: 0 })
}
