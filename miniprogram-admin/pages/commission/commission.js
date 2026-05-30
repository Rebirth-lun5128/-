const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    platformTiers: [],
    districtTiers: [],
    savingPlatform: false,
    savingDistrict: false,
    previewSales: 5000,
    previewResult: '',
  },

  onLoad() {
    if (!app.isSuperAdmin()) {
      wx.showToast({ title: '仅超级管理员可访问', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1500)
      return
    }
    this.loadTiers()
  },

  async loadTiers() {
    try {
      const res = await api.get('/api/admin/commission-tiers')
      this.setData({
        platformTiers: (res.commission_tiers || []).map(t => ({
          min: String(t.min || 0), max: t.max === -1 ? '' : String(t.max || ''), rate: String(t.rate || 0),
        })),
        districtTiers: (res.district_commission_tiers || []).map(t => ({
          min: String(t.min || 0), max: t.max === -1 ? '' : String(t.max || ''), rate: String(t.rate || 0),
        })),
      })
    } catch (e) {}
  },

  // === 平台阶梯 ===
  addPlatformTier() {
    const tiers = this.data.platformTiers
    tiers.push({ min: '0', max: '', rate: '0.12' })
    this.setData({ platformTiers: tiers })
  },
  removePlatformTier(e) {
    const idx = e.currentTarget.dataset.index
    const tiers = this.data.platformTiers
    tiers.splice(idx, 1)
    this.setData({ platformTiers: tiers })
  },
  onPlatformMin(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ [`platformTiers[${idx}].min`]: e.detail.value })
  },
  onPlatformMax(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ [`platformTiers[${idx}].max`]: e.detail.value })
  },
  onPlatformRate(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ [`platformTiers[${idx}].rate`]: e.detail.value })
  },
  async savePlatform() {
    this.setData({ savingPlatform: true })
    try {
      const tiers = this.data.platformTiers.map(t => ({
        min: parseFloat(t.min) || 0,
        max: t.max === '' ? -1 : (parseFloat(t.max) || 0),
        rate: parseFloat(t.rate) || 0,
      }))
      await api.put('/api/admin/commission-tiers', tiers)
      wx.showToast({ title: '已保存', icon: 'success' })
    } catch (e) {} finally { this.setData({ savingPlatform: false }) }
  },

  // === 分区阶梯 ===
  addDistrictTier() {
    const tiers = this.data.districtTiers
    tiers.push({ min: '0', max: '', rate: '0.02' })
    this.setData({ districtTiers: tiers })
  },
  removeDistrictTier(e) {
    const idx = e.currentTarget.dataset.index
    const tiers = this.data.districtTiers
    tiers.splice(idx, 1)
    this.setData({ districtTiers: tiers })
  },
  onDistrictMin(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ [`districtTiers[${idx}].min`]: e.detail.value })
  },
  onDistrictMax(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ [`districtTiers[${idx}].max`]: e.detail.value })
  },
  onDistrictRate(e) {
    const idx = e.currentTarget.dataset.index
    this.setData({ [`districtTiers[${idx}].rate`]: e.detail.value })
  },
  async saveDistrict() {
    this.setData({ savingDistrict: true })
    try {
      const tiers = this.data.districtTiers.map(t => ({
        min: parseFloat(t.min) || 0,
        max: t.max === '' ? -1 : (parseFloat(t.max) || 0),
        rate: parseFloat(t.rate) || 0,
      }))
      await api.put('/api/admin/commission-tiers/district', tiers)
      wx.showToast({ title: '已保存', icon: 'success' })
    } catch (e) {} finally { this.setData({ savingDistrict: false }) }
  },

  // === 预览 ===
  onPreviewInput(e) {
    this.setData({ previewSales: parseFloat(e.detail.value) || 0 })
  },
  calcPreview() {
    const sales = this.data.previewSales
    let rate = 0.12, drate = 0
    const pt = this.data.platformTiers
    for (const t of pt) {
      const tmin = parseFloat(t.min) || 0
      const tmax = t.max === '' ? -1 : (parseFloat(t.max) || 0)
      if (sales >= tmin && (tmax < 0 || sales < tmax)) {
        rate = parseFloat(t.rate) || 0
        break
      }
    }
    const dt = this.data.districtTiers
    for (const t of dt) {
      const tmin = parseFloat(t.min) || 0
      const tmax = t.max === '' ? -1 : (parseFloat(t.max) || 0)
      if (sales >= tmin && (tmax < 0 || sales < tmax)) {
        drate = parseFloat(t.rate) || 0
        break
      }
    }
    const pf = sales * rate
    const df = sales * drate
    const net = sales - pf - df
    this.setData({
      previewResult: `平台${(rate*100).toFixed(0)}% ¥${pf.toFixed(2)} + 分区${(drate*100).toFixed(0)}% ¥${df.toFixed(2)} ＝ 商家得 ¥${net.toFixed(2)}`,
    })
  },
})
