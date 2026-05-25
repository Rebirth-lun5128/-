const api = require('../../utils/api')
const util = require('../../utils/util')

Page({
  data: {
    order: null,
    timeline: [],
  },

  onLoad(options) {
    this.setData({ orderId: options.id })
    this.loadOrder(options.id)
  },

  async loadOrder(id) {
    try {
      const order = await api.get(`/api/merchant/orders/${id}`)
      this.setData({
        order: { ...order, statusText: util.getOrderStatusText(order.status) },
        timeline: order.timeline || [],
      })
    } catch (e) { }
  },

  async acceptOrder() {
    try {
      await api.put(`/api/merchant/orders/${this.data.orderId}/accept`)
      wx.showToast({ title: '已接单', icon: 'success' })
      this.loadOrder(this.data.orderId)
    } catch (e) { }
  },

  async rejectOrder() {
    const res = await new Promise(r => wx.showModal({ title: '拒单确认', content: '确定拒接此单吗？', success: r }))
    if (!res.confirm) return
    try {
      await api.put(`/api/merchant/orders/${this.data.orderId}/reject?reason=商家拒单`)
      wx.showToast({ title: '已拒单', icon: 'success' })
      this.loadOrder(this.data.orderId)
    } catch (e) { }
  },

  async markReady() {
    try {
      await api.put(`/api/merchant/orders/${this.data.orderId}/ready`)
      wx.showToast({ title: '已出餐', icon: 'success' })
      this.loadOrder(this.data.orderId)
    } catch (e) { }
  },
})
