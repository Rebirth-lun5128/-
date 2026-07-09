import axios from 'axios'
import { showToast } from 'vant'

/** 创建指定角色的 API 实例 */
export function createApi(tokenKey = 'token', redirectPath = '#/login') {
  const http = axios.create({ baseURL: '', timeout: 15000 })

  http.interceptors.request.use((config) => {
    const token = localStorage.getItem(tokenKey)
    if (token) config.headers.Authorization = `Bearer ${token}`
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
        localStorage.removeItem(tokenKey)
        window.location.hash = redirectPath
      }
      return Promise.reject(err)
    },
  )

  return {
    get: (url, params, opts) => http.get(url, { params, ...opts }).then((r) => r.data),
    post: (url, data, opts) => http.post(url, data, opts).then((r) => r.data),
    put: (url, data, opts) => http.put(url, data, opts).then((r) => r.data),
    del: (url, opts) => http.delete(url, opts).then((r) => r.data),
  }
}

/** 用户端（默认） */
export const api = createApi('token', '#/login')

/** 商家端 */
export const merchantApi = createApi('merchant_token', '#/m/login')

/** 骑手端 */
export const riderApi = createApi('rider_token', '#/r/login')

export default api
