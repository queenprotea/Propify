import client from './client'

// user-service expuesto en el gateway bajo /api/users/
export const authApi = {
  login: (identifier, password) =>
    client.post('/users/login', { identifier, password }).then((r) => r.data),

  register: (data) =>
    client.post('/users/register', data).then((r) => r.data),

  registerAdmin: (data) =>
    client.post('/users/register/admin', data).then((r) => r.data),

  verifyToken: () => client.get('/users/verify-token').then((r) => r.data),
}
