const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    // Tab
    activeTab: 'orders',

    // 订单列表
    statusFilter: '',
    keyword: '',
    orders: [],
    loading: false,
    hasMore: true,

    // 修改审核
    modStatus: 'pending_review',
    modifications: [],
  },

  onLoad(options) {
    if (options.id) {
      // 如果是从其他页跳转过来带 id 参数，则直接跳到详情
      wx.navigateTo({ url: `/pages/order-detail/order-detail?id=${options.id}` })
    }
  },

  onShow() {
    if (!app.checkLogin()) return
    // 支持从首页通过 switchTab + globalData 传入筛选条件
    const filter = app.globalData.orderFilter
    if (filter) {
      if (filter.tab) this.setData({ activeTab: filter.tab })
      if (filter.status) this.setData({ statusFilter: filter.status })
      app.globalData.orderFilter = null
    }
    this.loadData()
  },

  // === Tab 切换 ===
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    this.setData({ activeTab: tab })
    this.loadData()
  },

  // === 订单列表 ===
  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
    clearTimeout(this._searchTimer)
    this._searchTimer = setTimeout(() => this.loadData(), 300)
  },

  onFilterTap(e) {
    const s = e.currentTarget.dataset.status
    this.setData({ statusFilter: s === this.data.statusFilter ? '' : s })
    this.loadData()
  },

  statusText(s) {
    const map = {
      pending_pay: '待支付', pending: '处理中',
      delivering: '配送中', completed: '已完成',
      cancelled: '已取消', partial: '部分完成',
    }
    return map[s] || s
  },

  async loadData() {
    this.setData({ loading: true })
    if (this.data.activeTab === 'modifications') {
      await this.loadModifications()
    } else {
      await this.loadOrders()
    }
    this.setData({ loading: false })
  },

  async loadOrders() {
    try {
      const params = {}
      if (this.data.statusFilter) params.status = this.data.statusFilter
      if (this.data.keyword) params.keyword = this.data.keyword
      const res = await api.get('/api/admin/orders', params)
      this.setData({
        orders: res.items || [],
        hasMore: (res.items || []).length >= 10,
      })
    } catch (e) {}
  },

  goToDetail(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/order-detail/order-detail?id=${id}` })
  },

  // === 修改审核 ===
  onModFilterTap(e) {
    const s = e.currentTarget.dataset.status
    this.setData({ modStatus: s === this.data.modStatus ? '' : s })
    this.loadModifications()
  },

  async loadModifications() {
    try {
      const params = {}
      if (this.data.modStatus) params.status = this.data.modStatus
      const res = await api.get('/api/admin/orders/modifications', params)
      this.setData({ modifications: res.items || [] })
    } catch (e) {}
  },

  async approveMod(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认同意',
      content: '确定同意该修改申请吗？',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.put(`/api/admin/orders/modifications/${id}/approve`)
          wx.showToast({ title: '已通过', icon: 'success' })
          this.loadModifications()
        } catch (e) {}
      },
    })
  },

  rejectMod(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '拒绝申请',
      content: '确定拒绝该修改申请吗？',
      editable: false,
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.put(`/api/admin/orders/modifications/${id}/reject`)
          wx.showToast({ title: '已拒绝', icon: 'success' })
          this.loadModifications()
        } catch (e) {}
      },
    })
  },
})
