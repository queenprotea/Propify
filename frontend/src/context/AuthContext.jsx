import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { authApi } from '../api/auth'
import { getToken, setToken } from '../api/client'
import { decodeJwt, isExpired } from '../utils/jwt'

const AuthContext = createContext(null)

function userFromToken(token) {
  if (!token || isExpired(token)) return null
  const claims = decodeJwt(token)
  if (!claims) return null
  return {
    id: Number(claims.sub),
    isAdmin: claims.is_admin === true,
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => userFromToken(getToken()))
  const [loading, setLoading] = useState(false)

  // Limpia sesión si el token caducó.
  useEffect(() => {
    const token = getToken()
    if (token && isExpired(token)) {
      setToken(null)
      setUser(null)
    }
  }, [])

  async function login(identifier, password) {
    setLoading(true)
    try {
      const data = await authApi.login(identifier, password)
      setToken(data.access_token)
      setUser(userFromToken(data.access_token))
      return userFromToken(data.access_token)
    } finally {
      setLoading(false)
    }
  }

  function logout() {
    setToken(null)
    setUser(null)
  }

  const value = useMemo(
    () => ({ user, loading, login, logout, isAuthenticated: !!user, isAdmin: !!user?.isAdmin }),
    [user, loading],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth debe usarse dentro de <AuthProvider>')
  return ctx
}
