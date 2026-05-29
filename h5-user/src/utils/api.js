import axios from 'axios'
import { showToast } from 'vant'

const http = axios.create({
  baseURL: '',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '网络错误'
    showToast({ message: msg, type: 'fail' })
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.hash = '#/login'
    }
    return Promise.reject(err)
  },
)

export const api = {
  get: (url, params) => http.get(url, { params }).then((r) => r.data),
  post: (url, data) => http.post(url, data).then((r) => r.data),
  put: (url, data) => http.put(url, data).then((r) => r.data),
  del: (url) => http.delete(url).then((r) => r.data),
}

export default http
