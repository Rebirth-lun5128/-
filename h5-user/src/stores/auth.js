import { reactive } from 'vue'

export const authStore = reactive({
  token: localStorage.getItem('token') || '',
  userInfo: JSON.parse(localStorage.getItem('userInfo') || 'null'),

  get isLogin() {
    return !!this.token
  },

  login(token, userInfo) {
    this.token = token
    this.userInfo = userInfo
    localStorage.setItem('token', token)
    localStorage.setItem('userInfo', JSON.stringify(userInfo))
  },

  logout() {
    this.token = ''
    this.userInfo = null
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
  },

  updateUserInfo(info) {
    this.userInfo = { ...this.userInfo, ...info }
    localStorage.setItem('userInfo', JSON.stringify(this.userInfo))
  },
})
