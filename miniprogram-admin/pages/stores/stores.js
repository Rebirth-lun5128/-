const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    tabs: ['全部', '待核验', '已通过', '已拒绝'],
    activeTab: 0,
    verifyMap: ['', 'unverified', 'verified', 'rejected'],
    stores: [],
    loading: false,
    keyword: '',

    // 抽成比例编辑
    editId: null,
    editRateVal: '',

    // 附加费编辑
    surchargeEditId: null,
    editSurchargeVal: '',
  },

  onShow() {
    if (!app.checkLogin()) return
    // 支持从首页通过 switchTab + globalData 传入筛选条件
    const filter = app.globalData.storeFilter
    if (filter === 'unverified') {
      this.setData({ activeTab: 1 })
      app.globalData.storeFilter = null
    } else if (filter === null) {
      this.setData({ activeTab: 0 })
      app.globalData.storeFilter = undefined
    }
    this.loadData()
  },

  onTabTap(e) {
    this.setData({ activeTab: e.currentTarget.dataset.index })
    this.loadData()
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
    clearTimeout(this._searchTimer)
    this._searchTimer = setTimeout(() => this.loadData(), 300)
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const params = {}
      const v = this.data.verifyMap[this.data.activeTab]
      if (v) params.verify_status = v
      if (this.data.keyword) params.keyword = this.data.keyword
      const res = await api.get('/api/admin/stores', params)
      const items = (res.items || []).map(s => ({
        ...s,
        commission_rate_display: ((s.commission_rate || 0.12) * 100).toFixed(1),
      }))
      this.setData({ stores: items })
    } catch (e) { } finally { this.setData({ loading: false }) }
  },

  // === 抽成比例编辑 ===
  startEditRate(e) {
    const { id, rate } = e.currentTarget.dataset
    this.setData({
      editId: id,
      editRateVal: ((rate || 0.12) * 100).toFixed(1),
      surchargeEditId: null,
    })
  },

  onRateInput(e) {
    this.setData({ editRateVal: e.detail.value })
  },

  async saveRate(e) {
    const id = e.currentTarget.dataset.id
    const rate = parseFloat(this.data.editRateVal) / 100
    if (isNaN(rate) || rate < 0 || rate > 1) {
      wx.showToast({ title: '请输入0-100之间的值', icon: 'none' })
      return
    }
    try {
      await api.put(`/api/admin/stores/${id}/commission-rate`, null, { rate })
      wx.showToast({ title: '抽成比例已更新', icon: 'success' })
      this.setData({ editId: null })
      this.loadData()
    } catch (e) { }
  },

  cancelEdit() {
    this.setData({ editId: null })
  },

  // === 附加费编辑 ===
  startEditSurcharge(e) {
    const { id, val } = e.currentTarget.dataset
    this.setData({
      surchargeEditId: id,
      editSurchargeVal: String(val || 0),
      editId: null,
    })
  },

  onSurchargeInput(e) {
    this.setData({ editSurchargeVal: e.detail.value })
  },

  async saveSurcharge(e) {
    const id = e.currentTarget.dataset.id
    const surcharge = parseFloat(this.data.editSurchargeVal) || 0
    try {
      await api.put(`/api/admin/stores/${id}/delivery-surcharge`, null, { surcharge })
      wx.showToast({ title: '附加费已更新', icon: 'success' })
      this.setData({ surchargeEditId: null })
      this.loadData()
    } catch (e) { }
  },

  cancelSurchargeEdit() {
    this.setData({ surchargeEditId: null })
  },
})
