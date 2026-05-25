const app = getApp()

Page({
  data: {
    userInfo: null,
  },

  onShow() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
    this.setData({ userInfo: app.globalData.userInfo })
  },

  goToAddress() {
    wx.navigateTo({ url: '/pages/address/address' })
  },

  goToOrders() {
    wx.switchTab({ url: '/pages/orders/orders' })
  },

  logout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出吗？',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('token')
          app.globalData.token = ''
          app.globalData.userInfo = null
          wx.navigateTo({ url: '/pages/login/login' })
        }
      },
    })
  },
})
