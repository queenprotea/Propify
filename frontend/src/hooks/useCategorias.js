import { useEffect, useState } from 'react'
import { propertiesApi } from '../api/properties'
import { TIPOS, OPERACIONES, USOS, ESTADOS } from '../utils/constants'

const fallback = { tipos: TIPOS, operaciones: OPERACIONES, usos: USOS, estados: ESTADOS }
let cache = null

// Carga los catálogos normalizados desde el backend (con fallback a constantes).
export function useCategorias() {
  const [cat, setCat] = useState(cache || fallback)
  useEffect(() => {
    if (cache) return
    let activo = true
    propertiesApi.categorias()
      .then((data) => {
        cache = {
          tipos: data.tipos?.length ? data.tipos : TIPOS,
          operaciones: data.operaciones?.length ? data.operaciones : OPERACIONES,
          usos: data.usos?.length ? data.usos : USOS,
          estados: data.estados?.length ? data.estados : ESTADOS,
        }
        if (activo) setCat(cache)
      })
      .catch(() => { /* se mantiene el fallback */ })
    return () => { activo = false }
  }, [])
  return cat
}
