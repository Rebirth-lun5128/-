const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    items: [],
    page: 1,
    hasMore: true,
    loading: false,
    showRejectModal: false,
    rejectModalId: 0,
    rejectModalValue: '',
  },

  onShow() {
    if (!app.checkLogin()) return
    this.setData({ page: 1, items: [], hasMore: true })
    this.loadData()
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) this.loadData()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, items: [], hasMore: true })
    this.loadData().then(() => wx.stopPullDownRefresh())
  },

  async loadData() {
    if (this.data.loading) return
    this.setData({ loading: true })
    try {
      const res = await api.get('/api/merchant/orders/modifications', {
        page: this.data.page,
        page_size: 10,
      })
      const items = (res.items || []).map(m => ({
        ...m,
        typeText: { cancel: '退单申请', address_change: '修改地址', refund: '退款申请', other: '其他申请' }[m.type] || m.type,
      }))
      this.setData({
        items: this.data.page === 1 ? items : [...this.data.items, ...items],
        page: this.data.page + 1,
        hasMore: items.length === 10,
      })
    } catch (e) { } finally {
      this.setData({ loading: false })
    }
  },

  async onApprove(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认同意',
      content: '同意该修改申请后，将执行相应操作（如退单将取消子单）',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.put(`/api/merchant/orders/modifications/${id}/approve`)
            wx.showToast({ title: '已同意', icon: 'success' })
            this.loadData()
          } catch (e) { }
        }
      },
    })
  },

  onReject(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ showRejectModal: true, rejectModalId: id, rejectModalValue: '' })
  },

  onRejectModalInput(e) {
    this.setData({ rejectModalValue: e.detail.value })
  },

  onRejectModalCancel() {
    this.setData({ showRejectModal: false, rejectModalValue: '' })
  },

  async onRejectModalConfirm() {
    const { rejectModalId, rejectModalValue } = this.data
    this.setData({ showRejectModal: false, rejectModalValue: '' })
    try {
      const comment = rejectModalValue.trim()
      await api.put(`/api/merchant/orders/modifications/${rejectModalId}/reject?comment=${encodeURIComponent(comment)}`)
      wx.showToast({ title: '已拒绝', icon: 'success' })
      this.setData({ page: 1, items: [], hasMore: true })
      this.loadData()
    } catch (e) { }
  },
})
