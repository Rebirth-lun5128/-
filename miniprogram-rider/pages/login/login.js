const api = require('../../utils/api')
const app = getApp()

Page({
  data: { phone: '', password: '' },

  onLoad() {
    if (app.globalData.token) {
      wx.switchTab({ url: '/pages/index/index' })
    }
  },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onPwdInput(e) { this.setData({ password: e.detail.value }) },

  async doLogin() {
    const { phone, password } = this.data
    if (!phone || !password) {
      wx.showToast({ title: '请填写手机号和密码', icon: 'none' })
      return
    }
    try {
      const result = await api.post('/api/common/auth/phone', { phone, password })
      wx.setStorageSync('rider_token', result.token)
      app.globalData.token = result.token
      wx.switchTab({ url: '/pages/index/index' })
    } catch (e) { }
  },
})
