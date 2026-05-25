App({
  globalData: {
    shopInfo: null,
    token: '',
  },

  onLaunch() {
    const token = wx.getStorageSync('merchant_token')
    if (token) {
      this.globalData.token = token
    }
  },

  checkLogin() {
    if (!this.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' })
      return false
    }
    return true
  },
})
