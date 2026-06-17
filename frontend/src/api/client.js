import axios from 'axios'

// Capa de acceso a datos: instancia única de axios.
// baseURL '/api' lo resuelve el proxy (Vite en dev, nginx en prod) hacia el gateway.
const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

const TOKEN_KEY = 'propify_token'

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

// Inyecta el JWT en cada petición.
client.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Mensajes técnicos/en inglés del backend → texto claro y amigable para el usuario.
const MENSAJES = {
  'Incorrect credentials': 'Correo/teléfono o contraseña incorrectos.',
  'Not authorized': 'No tienes permisos para realizar esta acción.',
  'Not authenticated': 'Inicia sesión para continuar.',
  'Could not validate credentials': 'Tu sesión no es válida. Vuelve a iniciar sesión.',
  'Invalid or expired token': 'Tu sesión expiró. Vuelve a iniciar sesión.',
  'Service Unavailable, please try again later': 'El servicio no está disponible en este momento. Intenta más tarde.',
  'Internal Server Error': 'Ocurrió un error inesperado. Intenta de nuevo más tarde.',
  'Not Found': 'No se encontró el recurso solicitado.',
}

// Nombres de campo → etiqueta amigable para los errores de validación.
const CAMPOS = {
  nombre: 'Nombre', correo: 'Correo', telefono: 'Teléfono', password: 'Contraseña',
  titulo: 'Título', descripcion: 'Descripción', precio: 'Precio', monto: 'Monto',
  area_construccion: 'Área de construcción', area_terreno: 'Área de terreno',
  num_recamaras: 'Recámaras', num_banos: 'Baños', num_estacionamientos: 'Estacionamientos',
  niveles: 'Niveles', codigo_postal: 'Código postal', numero: 'Número', texto: 'Texto',
  fecha: 'Fecha', fecha_inicio: 'Fecha de inicio', fecha_fin: 'Fecha de fin',
  meses_plazo: 'Plazo (meses)', identifier: 'Correo o teléfono',
}

// Traduce los mensajes de validación de Pydantic más comunes (en inglés) al español.
function traducirValidacion(msg) {
  let m = (msg || '').replace(/^Value error,\s*/, '')
  if (/field required/i.test(m)) return 'es obligatorio'
  let mt
  if ((mt = m.match(/Input should be less than or equal to (\d+)/i))) return `no debe ser mayor que ${mt[1]}`
  if ((mt = m.match(/Input should be greater than or equal to (\d+)/i))) return `no debe ser menor que ${mt[1]}`
  if ((mt = m.match(/Input should be greater than (\d+)/i))) return `debe ser mayor que ${mt[1]}`
  if ((mt = m.match(/String should have at least (\d+) character/i))) return `debe tener al menos ${mt[1]} caracteres`
  if ((mt = m.match(/String should have at most (\d+) character/i))) return `no debe exceder ${mt[1]} caracteres`
  if (/Input should be a valid integer/i.test(m)) return 'debe ser un número entero'
  if (/Input should be a valid number/i.test(m)) return 'debe ser un número válido'
  if (/value is not a valid email/i.test(m)) return 'no tiene un formato válido'
  return m  // los validadores propios ya vienen en español
}

// Normaliza `detail` a un texto legible y amigable (FastAPI/Pydantic, técnicos en inglés, etc.).
function normalizarDetail(data) {
  if (!data || data.detail === undefined) return data
  const d = data.detail
  if (typeof d === 'string') {
    return { ...data, detail: MENSAJES[d.trim()] || d }
  }
  if (Array.isArray(d)) {
    const msgs = d.map((e) => {
      const raw = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : ''
      const campo = CAMPOS[raw] || raw
      const m = traducirValidacion(e.msg)
      return campo ? `${campo}: ${m}` : m
    })
    return { ...data, detail: msgs.join(' · ') }
  }
  return { ...data, detail: String(d) }
}

client.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response && error.response.status === 401) {
      setToken(null)
    }
    if (error.response && error.response.data) {
      error.response.data = normalizarDetail(error.response.data)
    } else if (!error.response) {
      // Sin respuesta del servidor (red caída / timeout): mensaje amigable.
      error.response = { data: { detail: 'No se pudo conectar con el servidor. Revisa tu conexión e intenta de nuevo.' } }
    }
    return Promise.reject(error)
  },
)

export default client
