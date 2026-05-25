const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    status: 'offline', // offline/online/busy
    pendingOrders: [],
    myOrder: null, // 当前配送中的订单
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadStatus()
    this.loadPendingOrders()
    this.loadMyOrder()
  },

  onPullDownRefresh() {
    Promise.all([this.loadPendingOrders(), this.loadMyOrder()]).then(() => wx.stopPullDownRefresh())
  },

  async loadStatus() {
    try {
      // 从钱包接口获取骑手状态
      const wallet = await api.get('/api/rider/orders/wallet')
      this.setData({ status: wallet.status || 'offline' })
    } catch (e) { }
  },

  async loadPendingOrders() {
    if (this.data.status === 'offline') return
    try {
      const res = await api.get('/api/rider/orders/pending', { page: 1, page_size: 20 })
      this.setData({ pendingOrders: res.items || [] })
    } catch (e) { }
  },

  async loadMyOrder() {
    try {
      const res = await api.get('/api/rider/orders/my', { page: 1, page_size: 1 })
      // 找配送中的订单
      const active = (res.items || []).find(o => o.status === 'delivering')
      this.setData({ myOrder: active || null })
    } catch (e) { }
  },

  async toggleStatus() {
    const newStatus = this.data.status === 'offline' ? 'online' : 'offline'
    try {
      await api.put(`/api/rider/orders/status?status=${newStatus}`)
      this.setData({ status: newStatus })
      if (newStatus === 'online') {
        this.loadPendingOrders()
      }
      wx.showToast({ title: newStatus === 'online' ? '已上线' : '已下线', icon: 'success' })
    } catch (e) { }
  },

  async acceptOrder(e) {
    const order = e.currentTarget.dataset.order
    try {
      await api.post(`/api/rider/orders/${order.id}/accept`)
      wx.showToast({ title: '接单成功', icon: 'success' })
      this.loadPendingOrders()
      this.loadMyOrder()
    } catch (e) { }
  },

  async markDelivered() {
    if (!this.data.myOrder) return
    wx.showModal({
      title: '确认送达',
      content: '确定该订单已送达吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.put(`/api/rider/orders/${this.data.myOrder.id}/deliver`)
            wx.showToast({ title: '已送达', icon: 'success' })
            this.setData({ myOrder: null })
            this.loadPendingOrders()
          } catch (e) { }
        }
      },
    })
  },

  goToOrderDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/order-detail/order-detail?id=${id}` })
  },
})
