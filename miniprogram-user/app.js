const { checkBackend } = require('./utils/config')

App({
  globalData: {
    userInfo: null,
    token: '',
    cart: {},
    backendOk: false,
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }
    const userInfo = wx.getStorageSync('userInfo')
    if (userInfo) {
      this.globalData.userInfo = userInfo
    }
    const cart = wx.getStorageSync('cart')
    if (cart) {
      this.globalData.cart = cart
    }

    checkBackend().then((ok) => {
      this.globalData.backendOk = ok
      if (!ok) {
        wx.showModal({
          title: '后端未连接',
          content: '请先双击运行 E:\\CC\\server\\启动后端.bat\n\n然后在浏览器打开 http://127.0.0.1:8000/health 确认显示 ok',
          showCancel: false,
        })
      }
    })
  },

  checkLogin() {
    if (!this.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' })
      return false
    }
    return true
  },
})
