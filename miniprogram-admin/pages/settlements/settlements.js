const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    items: [],
    filterStatus: 'pending',
    filterType: '',
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadData()
  },

  async loadData() {
    try {
      const params = {}
      if (this.data.filterStatus) params.status = this.data.filterStatus
      if (this.data.filterType) params.target_type = this.data.filterType
      const res = await api.get('/api/admin/settlements', params)
      this.setData({ items: res.items || [] })
    } catch (e) { }
  },

  onFilterStatus(e) {
    const s = e.currentTarget.dataset.status
    this.setData({ filterStatus: s })
    this.loadData()
  },

  onFilterType(e) {
    const t = e.currentTarget.dataset.type
    this.setData({ filterType: t })
    this.loadData()
  },

  onApprove(e) {
    const id = e.currentTarget.dataset.id
    const item = this.data.items.find(i => i.id === id)
    wx.showModal({
      title: '确认结算',
      content: `确认已线下打款 ¥${item.amount} 给 ${item.target_name}？\n确认后将扣减对方余额。`,
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.put(`/api/admin/settlements/${id}/approve`)
          wx.showToast({ title: '结算已确认', icon: 'success' })
          this.loadData()
        } catch (e) { }
      }
    })
  },
})
