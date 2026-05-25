const api = require('../../utils/api')
const util = require('../../utils/util')
const app = getApp()

Page({
  data: {
    tabs: ['全部', '新订单', '进行中', '已完成'],
    activeTab: 0,
    statusMap: ['', 'pending_accept', 'preparing,ready', 'completed,cancelled'],
    orders: [],
    page: 1,
    hasMore: true,
    loading: false,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.setData({ page: 1, orders: [], hasMore: true })
    this.loadOrders()
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadOrders()
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
      const statusStr = this.data.statusMap[this.data.activeTab]
      if (statusStr) params.status = statusStr

      const res = await api.get('/api/merchant/orders', params)
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
