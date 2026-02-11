import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds timeout
})

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth-storage')
  if (token) {
    try {
      const authData = JSON.parse(token)
      if (authData.state?.token) {
        config.headers.Authorization = `Bearer ${authData.state.token}`
      }
    } catch (e) {
      // Ignore parse errors
    }
  }
  return config
})

// Handle 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth-storage')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API endpoints
export const authAPI = {
  login: (email: string, password: string) =>
    api.post('/api/auth/login', { email, password }),
}

export const companiesAPI = {
  list: () => api.get('/api/companies/'),
  get: (id: string) => api.get(`/api/companies/${id}`),
  create: (data: { name: string; email: string }) => 
    api.post('/api/companies/', data),
  connectOAuth: (companyId: string, data: {
    access_token: string;
    refresh_token: string;
    n8n_credential_id?: string;
    expires_in?: number;
  }) => api.post(`/api/companies/${companyId}/connect-oauth`, data),
}

export const emailsAPI = {
  process: (data: any) => api.post('/api/emails/process', data),
  list: (params?: {
    company_id?: string
    function?: string
    priority_min?: number
    limit?: number
  }) => api.get('/api/emails/', { params }),
  getPriorityQueue: (limit?: number) =>
    api.get('/api/emails/priority-queue', { params: { limit } }),
  get: (id: string) => api.get(`/api/emails/${id}`),
}

export const draftsAPI = {
  list: (params?: { company_id?: string; status?: string; limit?: number }) =>
    api.get('/api/drafts/', { params }),
  getPending: (params?: { company_id?: string; limit?: number }) =>
    api.get('/api/drafts/pending', { params }),
  get: (id: string) => api.get(`/api/drafts/${id}`),
  getStatus: (id: string) => api.get(`/api/drafts/${id}/status`),
  approve: (id: string, data?: { edited_body?: string }) =>
    api.post(`/api/drafts/${id}/approve`, { draft_id: id, ...data }),
  reject: (id: string) => api.post(`/api/drafts/${id}/reject`),
}

export const dashboardAPI = {
  getStats: () => api.get('/api/dashboard/stats'),
}

