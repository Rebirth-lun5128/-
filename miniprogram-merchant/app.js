const { checkBackend } = require('./utils/config')

App({
  globalData: {
    shopInfo: null,
    token: '',
    backendOk: false,
  },

  onLaunch() {
    const token = wx.getStorageSync('merchant_token')
    if (token) {
      this.globalData.token = token
    }

    checkBackend().then((ok) => {
      this.globalData.backendOk = ok
      if (!ok) {
        wx.showModal({
          title: '后端未连接',
          content: '请先双击运行 server\\启动后端.bat\n\n浏览器打开 http://127.0.0.1:8000/health 应显示 ok',
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
