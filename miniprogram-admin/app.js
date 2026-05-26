App({
  globalData: {
    userInfo: null,
    token: '',
  },

  onLaunch() {
    const token = wx.getStorageSync('admin_token')
    if (token) {
      this.globalData.token = token
    }
  },

  checkLogin() {
    if (!this.globalData.token) {
      wx.redirectTo({ url: '/pages/login/login' })
      return false
    }
    return true
  },

  logout() {
    this.globalData.token = ''
    wx.removeStorageSync('admin_token')
    wx.redirectTo({ url: '/pages/login/login' })
  },
})
