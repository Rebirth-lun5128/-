import axios from 'axios'
import { showToast } from 'vant'

/** 创建指定角色的 API 实例 */
export function createApi(tokenKey = 'token', redirectPath = '#/login') {
  const http = axios.create({ baseURL: '', timeout: 15000 })
  const refreshTokenKey = tokenKey + '_refresh'

  let refreshPromise = null  // 并发锁：同一时刻只允许一个 refresh 请求

  http.interceptors.request.use((config) => {
    const token = localStorage.getItem(tokenKey)
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })

  http.interceptors.response.use(
    (res) => res,
    async (err) => {
      const status = err.response?.status
      const isGet = err.config?.method?.toLowerCase() === 'get'
      // GET 请求自动 silent（查询类失败不踢人），显式 silent 也生效
      const silent = !!err.config?.silent || isGet
      const isRefreshRequest = err.config?.url?.includes('/api/common/auth/refresh')
      const serverMsg = err.response?.data?.detail || ''

      // 403 权限不足：不需要 refresh（续期也修不了权限），直接显示错误
      if (status === 403 && !isRefreshRequest) {
        if (!silent) showToast({ message: serverMsg || '权限不足', type: 'fail' })
        return Promise.reject(err)
      }

      // 401 token 过期 → 尝试自动 refresh
      if (status === 401 && !isRefreshRequest) {
        const storedRefreshToken = localStorage.getItem(refreshTokenKey)

        if (storedRefreshToken) {
          if (!refreshPromise) {
            refreshPromise = (async () => {
              try {
                const res = await axios.post('/api/common/auth/refresh', {
                  refresh_token: storedRefreshToken,
                })
                const { token, refresh_token: newRefresh } = res.data
                localStorage.setItem(tokenKey, token)
                if (newRefresh) localStorage.setItem(refreshTokenKey, newRefresh)
                return token
              } catch (e) {
                if (e.response?.status === 401) {
                  localStorage.removeItem(tokenKey)
                  localStorage.removeItem(refreshTokenKey)
                }
                throw new Error('refresh_failed')
              } finally {
                refreshPromise = null
              }
            })()
          }

          try {
            const newToken = await refreshPromise
            err.config.headers.Authorization = `Bearer ${newToken}`
            return http.request(err.config)
          } catch {
            if (!silent) {
              showToast({ message: '登录已过期，请重新登录', type: 'fail' })
              window.location.hash = redirectPath
            }
            return Promise.reject(err)
          }
        }

        if (!silent) {
          localStorage.removeItem(tokenKey)
          showToast({ message: '登录已过期，请重新登录', type: 'fail' })
          window.location.hash = redirectPath
        }
        return Promise.reject(err)
      }

      // 其他错误
      if (!silent) {
        showToast({ message: serverMsg || err.message || '网络错误', type: 'fail' })
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
