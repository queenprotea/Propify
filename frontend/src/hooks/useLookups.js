import { useEffect, useState } from 'react'
import { usersApi } from '../api/users'
import { propertiesApi } from '../api/properties'

// Caché a nivel de módulo (compartida entre componentes durante la sesión).
const userCache = new Map()
const propCache = new Map()

// Resuelve ids de usuario e inmueble a información legible
export function useLookups(userIds = [], propIds = []) {
  const [users, setUsers] = useState({})
  const [props, setProps] = useState({})

  const userKey = [...new Set(userIds.filter(Boolean))].sort().join(',')
  const propKey = [...new Set(propIds.filter(Boolean))].sort().join(',')

  useEffect(() => {
    let activo = true
    const ids = userKey ? userKey.split(',').map(Number) : []
    Promise.all(ids.map(async (id) => {
      if (!userCache.has(id)) {
        try { userCache.set(id, await usersApi.get(id)) } catch { userCache.set(id, null) }
      }
      return [id, userCache.get(id)]
    })).then((pairs) => { if (activo) setUsers(Object.fromEntries(pairs)) })
    return () => { activo = false }
  }, [userKey])

  useEffect(() => {
    let activo = true
    const ids = propKey ? propKey.split(',').map(Number) : []
    Promise.all(ids.map(async (id) => {
      if (!propCache.has(id)) {
        try { propCache.set(id, await propertiesApi.get(id)) } catch { propCache.set(id, null) }
      }
      return [id, propCache.get(id)]
    })).then((pairs) => { if (activo) setProps(Object.fromEntries(pairs)) })
    return () => { activo = false }
  }, [propKey])

  function userLabel(id) {
    const u = users[id]
    return u ? `${u.nombre} (${u.correo})` : `Usuario #${id}`
  }
  function propLabel(id) {
    const p = props[id]
    return p ? p.titulo : `Inmueble #${id}`
  }

  return { users, props, userLabel, propLabel }
}
