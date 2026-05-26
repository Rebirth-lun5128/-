const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    tabs: ['全部', '待审核', '已通过', '已拒绝'],
    activeTab: 1,
    auditMap: ['', 'pending', 'approved', 'rejected'],
    riders: [],
    loading: false,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadData()
  },

  onTabTap(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ activeTab: idx })
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const params = {}
      const s = this.data.auditMap[this.data.activeTab]
      if (s) params.audit_status = s
      const res = await api.get('/api/admin/riders', params)
      this.setData({ riders: res.items || [] })
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },

  async doAudit(e) {
    const { id, status } = e.currentTarget.dataset
    const label = status === 'approved' ? '通过' : '拒绝'
    wx.showModal({
      title: `确认${label}`,
      content: `确定${label}该骑手的审核申请吗？`,
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.put(`/api/admin/riders/${id}/audit`, null, { audit_status: status })
          wx.showToast({ title: `已${label}`, icon: 'success' })
          this.loadData()
        } catch (e) {}
      },
    })
  },
})
