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

  updateStatus: (id, estadoId) =>
    client.patch(`${base}/inmuebles/${id}/estado/${estadoId}`).then((r) => r.data),

  updateStatusByValor: (id, valor) =>
    client.patch(`${base}/inmuebles/${id}/estado-valor/${encodeURIComponent(valor)}`).then((r) => r.data),

  remove: (id) => client.delete(`${base}/inmuebles/${id}`).then((r) => r.data),

  categorias: () => client.get(`${base}/categorias`).then((r) => r.data),
}

export const locationsApi = {
  get: (id) => client.get(`${base}/ubicaciones/id/${id}`).then((r) => r.data),
  create: (data) => client.post(`${base}/ubicaciones`, data).then((r) => r.data),
  update: (id, data) => client.put(`${base}/ubicaciones/${id}`, data).then((r) => r.data),
}

export const imagesApi = {
  byInmueble: (id) => client.get(`${base}/imagenes/inmueble/${id}`).then((r) => r.data),
  upload: (inmuebleId, file, descripcion) => {
    const form = new FormData()
    form.append('descripcion', descripcion)
    form.append('file', file)
    return client
      .post(`${base}/imagenes/${inmuebleId}`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
      .then((r) => r.data)
  },
  remove: (id) => client.delete(`${base}/imagenes/${id}`).then((r) => r.data),
}

export const historyApi = {
  byInmueble: (id) => client.get(`${base}/historial-estado/inmueble/${id}`).then((r) => r.data),
  current: (id) => client.get(`${base}/historial-estado/inmueble/${id}/actual`).then((r) => r.data),
  create: (data) => client.post(`${base}/historial-estado`, data).then((r) => r.data),
}

export const contactsApi = {
  create: (data) => client.post(`${base}/contactos`, data).then((r) => r.data),
  all: (limit = 100, offset = 0) =>
    client.get(`${base}/contactos/all`, { params: { limit, offset } }).then((r) => r.data),
  byInmueble: (id) => client.get(`${base}/contactos/inmueble/${id}`).then((r) => r.data),
}
