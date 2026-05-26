const api = require('../../utils/api')

Page({
  data: {
    order: null,
    orderId: null,
    loading: true,
  },

  onLoad(options) {
    this.setData({ orderId: options.id })
    this.loadOrder()
  },

  statusText(s) {
    const map = {
      pending_pay: '待支付', pending: '处理中',
      delivering: '配送中', completed: '已完成',
      cancelled: '已取消', partial: '部分完成',
      pending_accept: '待接单', preparing: '备餐中',
      ready: '待取餐',
    }
    return map[s] || s
  },

  async loadOrder() {
    this.setData({ loading: true })
    try {
      const res = await api.get(`/api/admin/orders/${this.data.orderId}/detail`)
      this.setData({ order: res })
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },

  forceCancel() {
    wx.showModal({
      title: '强制取消订单',
      content: '确定强制取消此订单吗？此操作不可撤销。',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.put(`/api/admin/orders/${this.data.orderId}/force-cancel`)
          wx.showToast({ title: '已取消', icon: 'success' })
          setTimeout(() => this.loadOrder(), 800)
        } catch (e) {}
      },
    })
  },
})
