import client from './client'

// contract-service bajo /api/contracts/
export const contractsApi = {
  get: (id) => client.get(`/contracts/contratos/${id}`).then((r) => r.data),
  byUser: (userId) => client.get(`/contracts/contratos/usuario/${userId}`).then((r) => r.data),
  byProperty: (id) => client.get(`/contracts/contratos/inmueble/${id}`).then((r) => r.data),
  create: (data) => client.post('/contracts/contratos', data).then((r) => r.data),

  // Gestión administrativa (M1/M2)
  listAll: (params = {}) => client.get('/contracts/contratos', { params }).then((r) => r.data),
  setEstado: (id, estado) => client.patch(`/contracts/contratos/${id}/estado`, { estado }).then((r) => r.data),
  validarDocumento: (id, data) => client.post(`/contracts/contratos/${id}/documento`, data).then((r) => r.data),
  finalizar: (id) => client.patch(`/contracts/contratos/${id}/finalizar`).then((r) => r.data),
  cancelar: (id) => client.patch(`/contracts/contratos/${id}/cancelar`).then((r) => r.data),

  // Pagos / calendario / resumen
  payments: (id) => client.get(`/contracts/contratos/${id}/pagos`).then((r) => r.data),
  addPayment: (contratoId, data) =>
    client.post(`/contracts/contratos/${contratoId}/pagos`, data).then((r) => r.data),
  addPaymentTransferencia: (contratoId, monto, file, numeroCuota) => {
    const form = new FormData()
    form.append('monto', monto)
    if (numeroCuota != null) form.append('numero_cuota', numeroCuota)
    form.append('file', file)
    return client
      .post(`/contracts/contratos/${contratoId}/pagos/transferencia`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
      .then((r) => r.data)
  },
  verificarPago: (pagoId, data) =>
    client.patch(`/contracts/pagos/${pagoId}/verificar`, data).then((r) => r.data),
  pagarStripe: (contratoId, data) =>
    client.post(`/contracts/contratos/${contratoId}/pagos/stripe`, data).then((r) => r.data),
  resumen: (id) => client.get(`/contracts/contratos/${id}/resumen`).then((r) => r.data),

  // PDF original (blob, con JWT)
  pdfBlob: (id) =>
    client.get(`/contracts/contratos/${id}/pdf`, { responseType: 'blob' }).then((r) => r.data),

  // Subir / descargar contrato firmado
  uploadSigned: (id, file) => {
    const form = new FormData()
    form.append('file', file)
    return client
      .post(`/contracts/contratos/${id}/firmado`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
      .then((r) => r.data)
  },
  signedBlob: (id) =>
    client.get(`/contracts/contratos/${id}/firmado`, { responseType: 'blob' }).then((r) => r.data),

  // Comprobantes de pago (se generan ligados a un pago por transferencia; aquí solo se listan/descargan)
  comprobantes: (id) => client.get(`/contracts/contratos/${id}/comprobantes`).then((r) => r.data),
  comprobanteBlob: (compId) =>
    client.get(`/contracts/comprobantes/${compId}/archivo`, { responseType: 'blob' }).then((r) => r.data),
}

// Solicitudes de renta
export const rentalsApi = {
  create: (data) => client.post('/contracts/solicitudes', data).then((r) => r.data),
  all: () => client.get('/contracts/solicitudes').then((r) => r.data),
  byUser: (userId) => client.get(`/contracts/solicitudes/usuario/${userId}`).then((r) => r.data),
  get: (id) => client.get(`/contracts/solicitudes/${id}`).then((r) => r.data),
  setEstado: (id, estado) =>
    client.patch(`/contracts/solicitudes/${id}/estado`, { estado }).then((r) => r.data),
  cancel: (id) => client.patch(`/contracts/solicitudes/${id}/cancelar`).then((r) => r.data),
  generarContrato: (id, data) =>
    client.post(`/contracts/solicitudes/${id}/contrato`, data).then((r) => r.data),
  generarContratoVenta: (id, data) =>
    client.post(`/contracts/solicitudes/${id}/contrato-venta`, data).then((r) => r.data),
}

// Catálogo de cláusulas (jerárquicas) para contratos
export const clausesApi = {
  list: () => client.get('/contracts/clausulas-catalogo').then((r) => r.data),
  create: (data) => client.post('/contracts/clausulas-catalogo', data).then((r) => r.data),
  remove: (id) => client.delete(`/contracts/clausulas-catalogo/${id}`).then((r) => r.data),
}

// Descarga un blob en el navegador.
export function descargarBlob(blob, nombre) {
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = nombre
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}
