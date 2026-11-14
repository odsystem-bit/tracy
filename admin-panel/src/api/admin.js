import client from './client'

export const adminApi = {
  // Dashboard
  getDashboard: () =>
    client.get('/admin/dashboard'),

  getLiveFeed: (page = 1) =>
    client.get('/admin/live-feed', { params: { page } }),

  // Users
  getUsers: (params = {}) =>
    client.get('/admin/users', { params }),

  getUser: (id) =>
    client.get(`/admin/users/${id}`),

  toggleBan: (id) =>
    client.patch(`/admin/users/${id}/ban`),

  // Orders
  getOrders: (params = {}) =>
    client.get('/admin/orders', { params }),

  // Restaurants
  getRestaurants: (params = {}) =>
    client.get('/admin/restaurants', { params }),

  // Finance
  getFinance: () =>
    client.get('/admin/finance'),

  // Tracy Core
  getTracyStatus: () =>
    client.get('/admin/tracy/status'),

  getTracyConfig: () =>
    client.get('/admin/tracy/config'),

  // Growth
  getGrowth: () =>
    client.get('/admin/growth'),

  // Revenue
  getRevenue: () =>
    client.get('/admin/revenue'),

  // Countries
  getCountries: () =>
    client.get('/admin/countries'),

  // Shops map
  getShopsMap: (params = {}) =>
    client.get('/admin/shops-map', { params }),

  // Shop quality
  getShopQuality: () =>
    client.get('/admin/shop-quality'),

  // Security
  getSecurity: () =>
    client.get('/admin/security'),

  // System health
  getSystemHealth: () =>
    client.get('/admin/system-health'),

  // Notifications
  getNotifications: () =>
    client.get('/admin/notifications'),

  // Knowledge Gaps (RAG Correctif)
  getKnowledgeGaps: (params = {}) =>
    client.get('/admin/knowledge/gaps', { params }),
  updateKnowledgeGap: (id, data) =>
    client.patch(`/admin/knowledge/gaps/${id}`, data),
}
