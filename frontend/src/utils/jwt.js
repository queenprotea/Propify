// Decodifica el payload de un JWT (solo lectura de claims, sin verificar firma).
export function decodeJwt(token) {
  try {
    const payload = token.split('.')[1]
    const json = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    return JSON.parse(json)
  } catch {
    return null
  }
}

export function isExpired(token) {
  const data = decodeJwt(token)
  if (!data || !data.exp) return true
  return Date.now() >= data.exp * 1000
}
