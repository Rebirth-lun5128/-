import { reactive } from 'vue'
import { api } from '../utils/api'

export const authStore = reactive({
  token: localStorage.getItem('token') || '',
  userInfo: JSON.parse(localStorage.getItem('userInfo') || 'null'),

  get isLogin() {
    return !!this.token
  },

  login(token, refreshToken, userInfo) {
    this.token = token
    this.userInfo = userInfo
    localStorage.setItem('token', token)
    if (refreshToken) localStorage.setItem('token_refresh', refreshToken)
    localStorage.setItem('userInfo', JSON.stringify(userInfo))
    // 记住上次登录手机号，方便下次自动填充
    if (userInfo?.phone) localStorage.setItem('last_login_phone', userInfo.phone)
  },

  logout() {
    this.token = ''
    this.userInfo = null
    localStorage.removeItem('token')
    localStorage.removeItem('token_refresh')
    localStorage.removeItem('userInfo')
    // 保留 last_login_phone 和 remembered_pwd，下次打开自动填充
  },

  updateUserInfo(info) {
    this.userInfo = { ...this.userInfo, ...info }
    localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
  },

  async refreshUser() {
    try {
      const info = await api.get('/api/common/auth/me', {}, { silent: true })
      this.userInfo = info
      localStorage.setItem('userInfo', JSON.stringify(info))
    } catch {}
  },
})
