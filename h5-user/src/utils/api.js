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
    if (!err.config?.silent) {
      const msg = err.response?.data?.detail || err.message || '网络错误'
      showToast({ message: msg, type: 'fail' })
    }
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      window.location.hash = '#/login'
    }
    return Promise.reject(err)
  },
)

export const api = {
  get: (url, params, opts) => http.get(url, { params, ...opts }).then((r) => r.data),
  post: (url, data, opts) => http.post(url, data, opts).then((r) => r.data),
  put: (url, data, opts) => http.put(url, data, opts).then((r) => r.data),
  del: (url, opts) => http.delete(url, opts).then((r) => r.data),
}

export default http
