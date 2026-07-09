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
      const status = err.response?.status
      if (status === 401 || status === 403) {
        // silent 模式下不踢登录，仅静默失败
        if (!err.config?.silent) {
          showToast({ message: '登录已过期，请重新登录', type: 'fail' })
          localStorage.removeItem(tokenKey)
          window.location.hash = redirectPath
        }
      } else if (!err.config?.silent) {
        const msg = err.response?.data?.detail || err.message || '网络错误'
        showToast({ message: msg, type: 'fail' })
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
