import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  headers: { 'Content-Type': 'application/json' },
})

// Auto-attach token from localStorage on every request (covers page refresh)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ccrts_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// API methods
export const authAPI = {
  register: (data) => api.post('/api/auth/register', data),
  login: (data) => api.post('/api/auth/login', data),
}

export const complaintsAPI = {
  list: (params = {}) => api.get('/api/complaints/', { params }),
  get: (id) => api.get(`/api/complaints/${id}`),
  create: (data) => api.post('/api/complaints/', data),
  assign: (id, agent_id) => api.put(`/api/complaints/${id}/assign`, { agent_id }),
  updateStatus: (id, new_status, comment) =>
    api.put(`/api/complaints/${id}/status`, { new_status, comment }),
  getHistory: (id) => api.get(`/api/complaints/${id}/history`),
}

export const categoriesAPI = {
  list: () => api.get('/api/categories/'),
}

export const usersAPI = {
  list: () => api.get('/api/users/'),
  listAgents: () => api.get('/api/users/agents'),
  getMe: () => api.get('/api/users/me'),
}

export const feedbackAPI = {
  submit: (complaint_id, data) => api.post(`/api/feedback/${complaint_id}`, data),
  get: (complaint_id) => api.get(`/api/feedback/${complaint_id}`),
}

export const dashboardAPI = {
  stats: () => api.get('/api/dashboard/stats'),
}

export default api
