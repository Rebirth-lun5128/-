const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    coupons: [],
    loading: false,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadData()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/api/admin/coupons')
      this.setData({ coupons: Array.isArray(res) ? res : (res.items || []) })
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },

  goToCreate() {
    wx.navigateTo({ url: '/pages/coupon-edit/coupon-edit' })
  },

  goToEdit(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/coupon-edit/coupon-edit?id=${id}` })
  },

  async toggleStatus(e) {
    const { id, status } = e.currentTarget.dataset
    const newLabel = status == 1 ? '停用' : '启用'
    wx.showModal({
      title: `确认${newLabel}`,
      content: `确定${newLabel}该优惠券吗？`,
      success: async (res) => {
        if (!res.confirm) return
        try {
          const result = await api.put(`/api/admin/coupons/${id}/toggle`)
          wx.showToast({ title: result.message || `已${newLabel}`, icon: 'success' })
          this.loadData()
        } catch (e) {}
      },
    })
  },
})
