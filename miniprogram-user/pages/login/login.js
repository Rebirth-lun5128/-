const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    canLogin: false,
  },

  onLoad() {
    // 检查是否已登录
    if (app.globalData.token) {
      wx.switchTab({ url: '/pages/index/index' })
    }
  },

  getPhoneNumber(e) {
    // 微信手机号授权 (需企业认证小程序)
    // 开发阶段使用模拟登录
    if (e.detail.errMsg === 'getPhoneNumber:ok') {
      this.doWechatLogin()
    }
  },

  doWechatLogin() {
    wx.login({
      success: async (res) => {
        if (!res.code) {
          wx.showToast({ title: '获取登录凭证失败', icon: 'none' })
          return
        }
        try {
          const result = await api.post('/api/common/auth/wechat', { code: res.code })
          wx.setStorageSync('token', result.token)
          wx.setStorageSync('userInfo', result.user)
          app.globalData.token = result.token
          app.globalData.userInfo = result.user
          wx.showToast({ title: '登录成功', icon: 'success' })
          setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 500)
        } catch (e) {
          wx.showToast({ title: '登录失败', icon: 'none' })
        }
      },
    })
  },

  /** 开发阶段: 绕过微信登录直接模拟 */
  mockLogin() {
    const mockCode = 'dev_code_' + Date.now()
    api.post('/api/common/auth/wechat', { code: mockCode }).then(result => {
      wx.setStorageSync('token', result.token)
      wx.setStorageSync('userInfo', result.user)
      app.globalData.token = result.token
      app.globalData.userInfo = result.user
      wx.showToast({ title: '登录成功', icon: 'success' })
      setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 500)
    }).catch(() => {
      wx.showModal({
        title: '无法连接后端',
        content: '请双击 server\\启动后端.bat 启动服务后重试',
        showCancel: false,
      })
    })
  },
})
