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
      const orders = (res.items || []).map(o => ({
        ...o,
        storeNames: (o.sub_orders || []).map(s => s.store_name || s.store_name_snapshot).join('、'),
        storeCount: (o.sub_orders || []).length,
      }))
      this.setData({ orders })
    } catch (e) { }
  },
})
