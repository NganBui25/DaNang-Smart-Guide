import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8080/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status
    const originalRequest = error.config || {}
    const refreshToken = localStorage.getItem('refresh_token')

    if (status === 401 && refreshToken && !originalRequest.__isRetryRequest) {
      originalRequest.__isRetryRequest = true
      try {
        const refreshResp = await axios.post(`${API_BASE}/auth/token/refresh/`, { refresh: refreshToken })
        const newAccess = refreshResp?.data?.access
        if (newAccess) {
          localStorage.setItem('access_token', newAccess)
          originalRequest.headers = originalRequest.headers || {}
          originalRequest.headers.Authorization = `Bearer ${newAccess}`
          return api(originalRequest)
        }
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
      }
    }

    const detail = error?.response?.data?.detail
    const message =
      detail ||
      error?.response?.data?.error ||
      (status ? `Loi ${status} tu server.` : 'Khong the ket noi den server.')

    return Promise.reject(new Error(message))
  }
)

export const placesApi = {
  list: (params = {}) => api.get('/places/', { params }),
  detail: (id) => api.get(`/places/${id}/`),
  reviews: (id) => api.get(`/places/${id}/reviews/`),
  submitReview: (payload) => api.post('/reviews/', payload),
  submit: (data) => api.post('/places/', data),
  bookmark: (id) => api.post(`/places/${id}/bookmark/`),
  bookmarks: () => api.get('/places/bookmarks/'),
}

export const searchApi = {
  semantic: (query, top_k = 10) =>
    api.post('/search/', { query, top_k }),
}

export const categoriesApi = {
  list: () => api.get('/categories/'),
}

export const authApi = {
  register: (payload) => api.post('/auth/register/', payload),
  login: (payload) => api.post('/auth/token/', payload),
  refresh: (refresh) => api.post('/auth/token/refresh/', { refresh }),
}

export default api
