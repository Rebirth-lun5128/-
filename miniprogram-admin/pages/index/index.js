const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    dashboard: null,
    chartStats: [],
    maxCount: 0,
    visits: { today: 0, yesterday: 0, total: 0 },
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadDashboard()
    this.loadStats()
    this.loadVisits()
    this.trackVisit()
  },

  async loadDashboard() {
    try {
      const res = await api.get('/api/admin/dashboard')
      this.setData({ dashboard: res })
    } catch (e) {}
  },

  async loadStats() {
    try {
      const res = await api.get('/api/admin/orders/stats', { days: 7 })
      const max = Math.max(...res.map(s => s.count), 1)
      this.setData({ chartStats: res, maxCount: max })
    } catch (e) {}
  },

  async loadVisits() {
    try {
      const res = await api.get('/api/admin/visits/stats', { days: 7 })
      this.setData({ visits: { today: res.today || 0, yesterday: res.yesterday || 0, total: res.total || 0 } })
    } catch (e) {}
  },

  trackVisit() {
    api.post('/api/admin/visits/track').catch(() => {})
  },

  // === 导航（非 tab 页用 navigateTo，tab 页用 switchTab + globalData） ===
  goCustomers() {
    wx.navigateTo({ url: '/pages/customers/customers' })
  },

  goStores() {
    app.globalData.storeFilter = null
    wx.switchTab({ url: '/pages/stores/stores' })
  },

  goStoresVerify() {
    app.globalData.storeFilter = 'unverified'
    wx.switchTab({ url: '/pages/stores/stores' })
  },

  goOrders() {
    app.globalData.orderFilter = null
    wx.switchTab({ url: '/pages/orders/orders' })
  },

  goOrdersPending() {
    app.globalData.orderFilter = { tab: 'orders', status: 'pending' }
    wx.switchTab({ url: '/pages/orders/orders' })
  },

  goOrdersModifications() {
    app.globalData.orderFilter = { tab: 'modifications', status: '' }
    wx.switchTab({ url: '/pages/orders/orders' })
  },
})
