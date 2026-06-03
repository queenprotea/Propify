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

// Normaliza los mensajes de error para que `detail` sea siempre un texto legible
// (FastAPI/Pydantic devuelve un array de errores en validaciones 422).
function normalizarDetail(data) {
  if (!data || data.detail === undefined) return data
  const d = data.detail
  if (typeof d === 'string') return data
  if (Array.isArray(d)) {
    const msgs = d.map((e) => {
      const campo = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : ''
      const m = (e.msg || '').replace(/^Value error,\s*/, '')
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
    }
    return Promise.reject(error)
  },
)

export default client
