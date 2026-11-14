import client from './client'

export const authApi = {
  login: (email, password) =>
    client.post('/admin/login', { email, password }),

  logout: () =>
    client.post('/admin/logout'),

  me: () =>
    client.get('/admin/me'),
}
