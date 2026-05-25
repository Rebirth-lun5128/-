const api = require('../../utils/api')
const util = require('../../utils/util')

Page({
  data: {
    order: null,
    timeline: [],
  },

  onLoad(options) {
    this.loadOrder(options.id)
  },

  async loadOrder(id) {
    try {
      const order = await api.get(`/api/user/orders/${id}`)
      this.setData({
        order: {
          ...order,
          statusText: util.getOrderStatusText(order.status),
          statusColor: util.getOrderStatusColor(order.status),
        },
        timeline: order.timeline || [],
      })
    } catch (e) { }
  },

  payOrder() {
    wx.showModal({
      title: '确认支付',
      content: `订单金额: ¥${this.data.order.total_price}`,
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.post(`/api/user/orders/${this.data.order.id}/pay`)
            wx.showToast({ title: '支付成功', icon: 'success' })
            this.loadOrder(this.data.order.id)
          } catch (e) { }
        }
      },
    })
  },

  cancelOrder() {
    wx.showModal({
      title: '取消订单',
      content: '确定要取消该订单吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.put(`/api/user/orders/${this.data.order.id}/cancel?reason=用户主动取消`)
            wx.showToast({ title: '已取消', icon: 'success' })
            this.loadOrder(this.data.order.id)
          } catch (e) { }
        }
      },
    })
  },
})
