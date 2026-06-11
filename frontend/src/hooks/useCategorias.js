import { useEffect, useState } from 'react'
import { propertiesApi } from '../api/properties'

const vacio = { tipos: [], estados: [], estados_republica: [] }
let cache = null

// Carga los catálogos normalizados ({id, valor}) desde el backend.
export function useCategorias() {
  const [cat, setCat] = useState(cache || vacio)
  useEffect(() => {
    if (cache) return
    let activo = true
    propertiesApi.categorias()
      .then((data) => {
        cache = {
          tipos: data.tipos || [],
          estados: data.estados || [],
          estados_republica: data.estados_republica || [],
        }
        if (activo) setCat(cache)
      })
      .catch(() => { /* se mantiene vacío */ })
    return () => { activo = false }
  }, [])
  return cat
}
