const api = require('../../utils/api')
const app = getApp()

Page({
  data: { phone: '', password: '', isRegister: false, showPwd: false },

  onLoad() {
    if (app.globalData.token) {
      wx.switchTab({ url: '/pages/index/index' })
    }
  },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onPwdInput(e) { this.setData({ password: e.detail.value }) },

  async doLogin() {
    const { phone, password, isRegister } = this.data
    if (!phone || !password) {
      wx.showToast({ title: '请填写手机号和密码', icon: 'none' })
      return
    }

    try {
      const url = isRegister ? '/api/common/auth/register' : '/api/common/auth/phone'
      const data = isRegister ? { phone, password, role: 'rider' } : { phone, password }
      const result = await api.post(url, data)
      wx.setStorageSync('rider_token', result.token)
      app.globalData.token = result.token
      wx.switchTab({ url: '/pages/index/index' })
    } catch (e) { }
  },

  toggleMode() {
    this.setData({ isRegister: !this.data.isRegister })
  },

  togglePwd() {
    this.setData({ showPwd: !this.data.showPwd })
  },
})
