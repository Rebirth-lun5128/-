const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    dashboard: null,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadDashboard()
  },

  async loadDashboard() {
    try {
      const res = await api.get('/api/merchant/shop/dashboard')
      this.setData({ dashboard: res })
    } catch (e) { }
  },

  goToOrders(e) {
    const status = e.currentTarget.dataset.status || ''
    wx.navigateTo({ url: `/pages/orders/orders?status=${status}` })
  },

  goToMenu() {
    wx.switchTab({ url: '/pages/menu/menu' })
  },

  goToShop() {
    wx.navigateTo({ url: '/pages/shop/shop' })
  },
})
