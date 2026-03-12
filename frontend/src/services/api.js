import axios from 'axios'

const API_BASE = 'http://localhost:8080/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
})

export const placesApi = {
  list: (params = {}) => api.get('/places/', { params }),
  detail: (id) => api.get(`/places/${id}/`),
  reviews: (id) => api.get(`/places/${id}/reviews/`),
  submit: (data) => api.post('/places/', data),
  bookmark: (id) => api.post(`/places/${id}/bookmark/`),
}

export const searchApi = {
  semantic: (query, top_k = 10) =>
    api.post('/search/', { query, top_k }),
}

export const categoriesApi = {
  list: () => api.get('/categories/'),
}

export default api
