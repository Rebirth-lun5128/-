App({
  globalData: {
    userInfo: null,
    token: '',
    cart: {}, // { restaurant_id: { items: [], restaurant_name: '' } }
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
    }
    const cart = wx.getStorageSync('cart')
    if (cart) {
      this.globalData.cart = cart
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
