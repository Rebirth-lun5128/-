const api = require('../../utils/api')
const app = getApp()

Page({
  data: { phone: '', password: '', showPwd: false, loading: false },

  onLoad() {
    if (app.globalData.token) {
      wx.switchTab({ url: '/pages/index/index' })
    }
  },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onPwdInput(e) { this.setData({ password: e.detail.value }) },

  togglePwd() {
    this.setData({ showPwd: !this.data.showPwd })
  },

  async doLogin() {
    if (!this.data.phone || !this.data.password) {
      wx.showToast({ title: '请输入手机号和密码', icon: 'none' })
      return
    }
    if (this.data.loading) return
    this.setData({ loading: true })
    try {
      const res = await api.post('/api/common/auth/phone', {
        phone: this.data.phone,
        password: this.data.password,
      })
      app.globalData.token = res.token
      wx.setStorageSync('admin_token', res.token)
      if (res.user) {
        app.globalData.role = res.user.role
        app.globalData.districtId = res.user.district_id || null
        wx.setStorageSync('admin_role', res.user.role)
        wx.setStorageSync('admin_district_id', res.user.district_id || null)
      }
      wx.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => {
        wx.switchTab({ url: '/pages/index/index' })
      }, 400)
    } catch (e) {
      // 错误提示由 api.js 统一处理
    } finally {
      this.setData({ loading: false })
    }
  },
})
