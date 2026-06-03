import client from './client'

const base = '/users'

export const usersApi = {
  all: (limit = 50, offset = 0) =>
    client.get(`${base}/users/all`, { params: { limit, offset } }).then((r) => r.data),

  active: (limit = 50, offset = 0) =>
    client.get(`${base}/users/active`, { params: { limit, offset } }).then((r) => r.data),

  get: (id) => client.get(`${base}/users/${id}`).then((r) => r.data),

  search: (q) => client.get(`${base}/users/search`, { params: { q } }).then((r) => r.data),

  update: (id, data) => client.put(`${base}/users/${id}`, data).then((r) => r.data),

  updateAsAdmin: (id, data) => client.put(`${base}/users/admin/${id}`, data).then((r) => r.data),

  activate: (id) => client.patch(`${base}/users/${id}/activate`).then((r) => r.data),

  deactivate: (id) => client.patch(`${base}/users/${id}/deactivate`).then((r) => r.data),
}

export const visitsApi = {
  all: () => client.get(`${base}/visits/all`).then((r) => r.data),
  get: (id) => client.get(`${base}/visits/id/${id}`).then((r) => r.data),
  byUser: (userId) => client.get(`${base}/visits/user/${userId}`).then((r) => r.data),
  byProperty: (id) => client.get(`${base}/visits/property/${id}`).then((r) => r.data),
  states: () => client.get(`${base}/visit-states/all`).then((r) => r.data),
  create: (data) => client.post(`${base}/visits`, data).then((r) => r.data),
  update: (id, data) => client.put(`${base}/visits/${id}`, data).then((r) => r.data),
}
