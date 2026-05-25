App({
  globalData: {
    riderInfo: null,
    token: '',
  },

  onLaunch() {
    const token = wx.getStorageSync('rider_token')
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
