const api = require('../../utils/api')
const app = getApp()

Page({
  data: { orders: [] },

  onShow() {
    if (!app.checkLogin()) return
    this.loadOrders()
  },

  async loadOrders() {
    try {
      const res = await api.get('/api/rider/orders/my', { page: 1, page_size: 50 })
      this.setData({ orders: res.items || [] })
    } catch (e) { }
  },
})
