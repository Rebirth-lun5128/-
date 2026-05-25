import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截: 添加 token
http.interceptors.request.use(config => {
  const token = localStorage.getItem('admin_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截: 统一错误处理
http.interceptors.response.use(
  res => res.data,
  err => {
    const msg = err.response?.data?.detail || '请求失败'
    ElMessage.error(msg)
    if (err.response?.status === 401) {
      localStorage.removeItem('admin_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default http
