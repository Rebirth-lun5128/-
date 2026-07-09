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
      const silent = !!err.config?.silent
      // 是否是 refresh 请求自身（避免死循环）
      const isRefreshRequest = err.config?.url?.includes('/api/common/auth/refresh')

      // 401/403 → 尝试自动 refresh
      if ((status === 401 || status === 403) && !isRefreshRequest) {
        const storedRefreshToken = localStorage.getItem(refreshTokenKey)

        if (storedRefreshToken) {
          // 并发锁：如果已有 refresh 在进行中，复用它的 Promise
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
                // 只有 refresh 接口明确返回 401/403 才清除 token（refresh_token 确实无效）
                // 网络错误等临时故障不清除，保留 token 下次再试
                if (e.response?.status === 401 || e.response?.status === 403) {
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
            // 用新 token 重试原请求
            err.config.headers.Authorization = `Bearer ${newToken}`
            return http.request(err.config)
          } catch {
            // refresh 失败，静默 reject（silent 模式）或踢登录
            if (!silent) {
              showToast({ message: '登录已过期，请重新登录', type: 'fail' })
              window.location.hash = redirectPath
            }
            return Promise.reject(err)
          }
        }

        // 没有 refresh_token，按 silent 模式决定行为
        if (!silent) {
          localStorage.removeItem(tokenKey)
          showToast({ message: '登录已过期，请重新登录', type: 'fail' })
          window.location.hash = redirectPath
        }
        return Promise.reject(err)
      }

      // 其他错误：silent 模式不弹 toast
      if (!silent) {
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
