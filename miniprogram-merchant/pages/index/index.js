const api = require('../../utils/api')
const ws = require('../../utils/websocket')
const app = getApp()

Page({
  data: {
    dashboard: null,
  },

  onLoad() {
    this._onOrderPaid = () => {
      wx.showToast({ title: '有新订单！', icon: 'none' })
      this.loadDashboard()
    }
    this._onOrderCancelled = () => {
      this.loadDashboard()
    }
    ws.on('order_paid', this._onOrderPaid)
    ws.on('order_cancelled', this._onOrderCancelled)
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadDashboard()
    if (app.globalData.backendOk) {
      ws.connect()
    }
  },

  onHide() {
    ws.close()
  },

  onUnload() {
    ws.off('order_paid', this._onOrderPaid)
    ws.off('order_cancelled', this._onOrderCancelled)
    ws.close()
  },

  async loadDashboard() {
    try {
      const res = await api.get('/api/merchant/shop/dashboard')
      this.setData({ dashboard: res })
    } catch (e) { }
  },

  async toggleStatus(e) {
    const checked = e.detail.value
    try {
      const res = await api.put('/api/merchant/shop/toggle-status')
      wx.showToast({ title: res.message, icon: 'success' })
      this.loadDashboard()
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

  goToModifications() {
    wx.navigateTo({ url: '/pages/modifications/modifications' })
  },

  onStatTap(e) {
    const type = e.currentTarget.dataset.type
    if (type === 'today_orders') {
      wx.navigateTo({ url: '/pages/orders/orders' })
    } else if (type === 'pending') {
      wx.navigateTo({ url: '/pages/orders/orders?status=pending_accept' })
    } else if (type === 'revenue') {
      wx.navigateTo({ url: '/pages/settlement/settlement' })
    } else if (type === 'monthly_sales') {
      wx.navigateTo({ url: '/pages/settlement/settlement' })
    }
  },
})
