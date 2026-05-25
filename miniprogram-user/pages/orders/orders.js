const api = require('../../utils/api')
const util = require('../../utils/util')
const app = getApp()

Page({
  data: {
    tabs: ['全部', '待接单', '配送中', '已完成'],
    activeTab: 0,
    statusMap: ['', 'pending_accept', 'delivering', 'completed'],
    orders: [],
    page: 1,
    hasMore: true,
    loading: false,
  },

  onShow() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
    this.setData({ page: 1, orders: [], hasMore: true })
    this.loadOrders()
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadOrders()
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, orders: [], hasMore: true })
    this.loadOrders().then(() => wx.stopPullDownRefresh())
  },

  async loadOrders() {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const params = { page: this.data.page, page_size: 10 }
      const status = this.data.statusMap[this.data.activeTab]
      if (status) params.status = status

      const res = await api.get('/api/user/orders', params)
      const orders = (res.items || []).map(o => ({
        ...o,
        statusText: util.getOrderStatusText(o.status),
        statusColor: util.getOrderStatusColor(o.status),
      }))

      this.setData({
        orders: this.data.page === 1 ? orders : [...this.data.orders, ...orders],
        page: this.data.page + 1,
        hasMore: orders.length < res.total,
      })
    } catch (e) { } finally {
      this.setData({ loading: false })
    }
  },

  onTabTap(e) {
    const index = e.currentTarget.dataset.index
    if (index === this.data.activeTab) return
    this.setData({ activeTab: index, page: 1, orders: [], hasMore: true })
    this.loadOrders()
  },

  onOrderTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/order-detail/order-detail?id=${id}` })
  },
})
