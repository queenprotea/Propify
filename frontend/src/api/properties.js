import client from './client'

// property-service bajo /api/properties/
const base = '/properties'

export const propertiesApi = {
  list: (limit = 100, offset = 0) =>
    client.get(`${base}/inmuebles/all`, { params: { limit, offset } }).then((r) => r.data),

  get: (id) => client.get(`${base}/inmuebles/id/${id}`).then((r) => r.data),

  disponibles: () => client.get(`${base}/inmuebles/disponible`).then((r) => r.data),

  byTipo: (tipo) => client.get(`${base}/inmuebles/tipo/${tipo}`).then((r) => r.data),

  byTitulo: (titulo) =>
    client.get(`${base}/inmuebles/titulo/${encodeURIComponent(titulo)}`).then((r) => r.data),

  create: (data) => client.post(`${base}/inmuebles`, data).then((r) => r.data),

  update: (id, data) => client.put(`${base}/inmuebles/${id}`, data).then((r) => r.data),

  updateStatus: (id, estado) =>
    client.patch(`${base}/inmuebles/id/${id}/status/${estado}`).then((r) => r.data),

  remove: (id) => client.delete(`${base}/inmuebles/${id}`).then((r) => r.data),

  categorias: () => client.get(`${base}/categorias`).then((r) => r.data),
  addCategoria: (catalogo, valor) =>
    client.post(`${base}/categorias/${catalogo}`, { valor }).then((r) => r.data),
  deleteCategoria: (catalogo, valor) =>
    client.delete(`${base}/categorias/${catalogo}/${encodeURIComponent(valor)}`).then((r) => r.data),
}

export const locationsApi = {
  get: (id) => client.get(`${base}/ubicaciones/${id}`).then((r) => r.data),
  create: (data) => client.post(`${base}/ubicaciones`, data).then((r) => r.data),
  update: (id, data) => client.put(`${base}/ubicaciones/${id}`, data).then((r) => r.data),
}

export const imagesApi = {
  byInmueble: (id) => client.get(`${base}/imagenes/inmueble/${id}`).then((r) => r.data),
  upload: (inmuebleId, file, textoAlternativo) => {
    const form = new FormData()
    form.append('inmueble_id', inmuebleId)
    form.append('texto_alternativo', textoAlternativo)
    form.append('file', file)
    return client
      .post(`${base}/imagenes`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
      .then((r) => r.data)
  },
  remove: (id) => client.delete(`${base}/imagenes/${id}`).then((r) => r.data),
}

export const historyApi = {
  byInmueble: (id) => client.get(`${base}/historial/inmueble/${id}`).then((r) => r.data),
  current: (id) => client.get(`${base}/historial/inmueble/${id}/actual`).then((r) => r.data),
  create: (data) => client.post(`${base}/historial`, data).then((r) => r.data),
}

export const contactsApi = {
  create: (data) => client.post(`${base}/contactos`, data).then((r) => r.data),
  all: (limit = 100, offset = 0) =>
    client.get(`${base}/contactos/all`, { params: { limit, offset } }).then((r) => r.data),
  byInmueble: (id) => client.get(`${base}/contactos/inmueble/${id}`).then((r) => r.data),
}
