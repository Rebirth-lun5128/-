const api = require('../../utils/api')

Page({
  data: {
    store: null,
    storeId: null,

    editingRate: false,
    editRateVal: '',

    editingSurcharge: false,
    editSurchargeVal: '',
  },

  onLoad(options) {
    this.setData({ storeId: options.id })
    this.loadStore()
  },

  async loadStore() {
    try {
      const res = await api.get('/api/admin/stores')
      const store = res.items.find(s => s.id == this.data.storeId)
      if (store) {
        store.commission_rate_display = ((store.commission_rate || 0.12) * 100).toFixed(1)
        store.created_at_display = (store.created_at || '').slice(0, 10)
        this.setData({ store })
      }
    } catch (e) { }
  },

  // === 抽成比例 ===
  startEditRate() {
    this.setData({
      editingRate: true,
      editingSurcharge: false,
      editRateVal: ((this.data.store.commission_rate || 0.12) * 100).toFixed(1),
    })
  },
  onRateInput(e) { this.setData({ editRateVal: e.detail.value }) },
  async saveRate() {
    const rate = parseFloat(this.data.editRateVal) / 100
    if (isNaN(rate) || rate < 0 || rate > 1) {
      wx.showToast({ title: '请输入0-100之间的值', icon: 'none' })
      return
    }
    try {
      await api.put(`/api/admin/stores/${this.data.storeId}/commission-rate`, null, { rate })
      wx.showToast({ title: '抽成已更新', icon: 'success' })
      this.setData({ editingRate: false })
      this.loadStore()
    } catch (e) { }
  },

  // === 附加费 ===
  startEditSurcharge() {
    this.setData({
      editingSurcharge: true,
      editingRate: false,
      editSurchargeVal: String(this.data.store.delivery_surcharge || 0),
    })
  },
  onSurchargeInput(e) { this.setData({ editSurchargeVal: e.detail.value }) },
  async saveSurcharge() {
    const surcharge = parseFloat(this.data.editSurchargeVal) || 0
    try {
      await api.put(`/api/admin/stores/${this.data.storeId}/delivery-surcharge`, null, { surcharge })
      wx.showToast({ title: '附加费已更新', icon: 'success' })
      this.setData({ editingSurcharge: false })
      this.loadStore()
    } catch (e) { }
  },

  cancelEdit() {
    this.setData({ editingRate: false, editingSurcharge: false })
  },

  // === 核验 ===
  async verify(e) {
    const { status, method } = e.currentTarget.dataset
    wx.showModal({
      title: status === 'verified' ? '确认通过核验' : '确认拒绝',
      content: method ? `核验方式: ${method}` : '',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.put(`/api/admin/stores/${this.data.storeId}/verify`, null, {
            verify_status: status,
            verify_method: method || '',
          })
          wx.showToast({ title: status === 'verified' ? '核验通过' : '已拒绝', icon: 'success' })
          this.loadStore()
        } catch (e) { }
      },
    })
  },

  async toggleStatus() {
    const s = this.data.store
    const newStatus = s.status === 'open' ? 'closed' : 'open'
    try {
      await api.put(`/api/admin/stores/${this.data.storeId}/toggle-status`, null, { status: newStatus })
      wx.showToast({ title: `已${newStatus === 'open' ? '开' : '关'}店`, icon: 'success' })
      this.loadStore()
    } catch (e) { }
  },
})
