const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    districts: [],
    editing: null,
    isSuperAdmin: true,
    form: {
      name: '', coverage: '', delivery_fee: 0, delivery_range: 3,
      notice: '', status: 1,
      peak_fee: 0, peak_start: '', peak_end: '',
    },
    ruleList: [],
    ruleTypes: ['🆓 满X免配送费', '💰 满X减Y'],
    hourOptions: Array.from({ length: 24 }, (_, i) => `${String(i).padStart(2, '0')}:00`),
  },

  onShow() {
    if (!app.checkLogin()) return
    this.setData({ isSuperAdmin: app.isSuperAdmin() })
    this.loadData()
  },

  async loadData() {
    try {
      const res = await api.get('/api/admin/districts')
      let districts = Array.isArray(res) ? res : (res.items || [])
      // 分区管理员只看自己的分区
      if (!app.isSuperAdmin() && app.globalData.districtId) {
        districts = districts.filter(d => d.id === app.globalData.districtId)
      }
      districts = districts.map(d => ({
        ...d,
        feeDisplay: (d.delivery_fee / 100).toFixed(1),
        peakFeeDisplay: (d.peak_delivery_fee / 100).toFixed(1),
      }))
      this.setData({ districts })
    } catch (e) {}
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  editDistrict(e) {
    const d = e.currentTarget.dataset.district
    this.setData({
      editing: d,
      form: {
        name: d.name || '',
        coverage: (d.coverage || []).join('、'),
        delivery_fee: ((d.delivery_fee || 0) / 100).toFixed(1),
        delivery_range: d.delivery_range || 3,
        notice: d.notice || '',
        status: d.status ?? 1,
        peak_fee: ((d.peak_delivery_fee || 0) / 100).toFixed(1),
        peak_start: d.peak_start_hour != null ? `${String(d.peak_start_hour).padStart(2, '0')}:00` : '',
        peak_end: d.peak_end_hour != null ? `${String(d.peak_end_hour).padStart(2, '0')}:00` : '',
      },
      ruleList: (d.delivery_fee_rules || []).map((r, i) => ({
        ...r, idx: i, threshold: Number(r.threshold) || 0, reduce: Number(r.reduce) || 0
      })),
    })
    wx.pageScrollTo({ scrollTop: 9999 })
  },

  resetForm() {
    this.setData({
      editing: null,
      form: {
        name: '', coverage: '', delivery_fee: 0, delivery_range: 3,
        notice: '', status: 1,
        peak_fee: 0, peak_start: '', peak_end: '',
      },
      ruleList: [],
    })
  },

  onSwitchStatus(e) {
    this.setData({ 'form.status': e.detail.value ? 1 : 0 })
  },

  // ====== 高峰时段 ======
  onPeakStart(e) {
    const idx = e.detail.value
    const hours = e.currentTarget.dataset.hours
    this.setData({ 'form.peak_start': hours[idx] })
  },
  onPeakEnd(e) {
    const idx = e.detail.value
    const hours = e.currentTarget.dataset.hours
    this.setData({ 'form.peak_end': hours[idx] })
  },

  // ====== 满减规则 ======
  addRule() {
    const list = this.data.ruleList
    list.push({ type: 'free', threshold: 20, reduce: 0, idx: Date.now() })
    this.setData({ ruleList: list })
  },

  removeRule(e) {
    const idx = e.currentTarget.dataset.idx
    const list = this.data.ruleList
    this.setData({ ruleList: list.filter(r => r.idx !== idx) })
  },

  onRuleTypeChange(e) {
    const idx = e.currentTarget.dataset.idx
    const type = e.detail.value === 0 ? 'free' : 'reduce'
    const list = this.data.ruleList
    const rule = list.find(r => r.idx === idx)
    if (rule) rule.type = type
    this.setData({ ruleList: list })
  },

  onRuleFieldInput(e) {
    const { idx, field } = e.currentTarget.dataset
    const val = parseInt(e.detail.value) || 0
    const list = this.data.ruleList
    const rule = list.find(r => r.idx === idx)
    if (rule) rule[field] = val
    this.setData({ ruleList: list })
  },

  async saveRules() {
    if (!this.data.editing) return
    const rules = this.data.ruleList
      .map(r => ({
        type: r.type,
        threshold: Number(r.threshold),
        reduce: r.type === 'reduce' ? Number(r.reduce) : 0,
        desc: r.type === 'free'
          ? `满${r.threshold}元免配送费`
          : `满${r.threshold}元减${r.reduce}元配送费`
      }))
      .sort((a, b) => b.threshold - a.threshold)
    try {
      await api.put(`/api/admin/districts/${this.data.editing.id}/delivery-rules`, rules)
      wx.showToast({ title: '规则已保存', icon: 'success' })
      this.loadData()
    } catch (e) {}
  },

  // ====== 保存 ======
  async saveDistrict() {
    const f = this.data.form
    if (!f.name.trim()) {
      wx.showToast({ title: '请输入分区名称', icon: 'none' })
      return
    }
    const coverage = f.coverage ? f.coverage.split(/[,，、\s]+/).filter(Boolean) : []
    const deliveryFeeFen = Math.round(parseFloat(f.delivery_fee) * 100) || 0
    const peakFeeFen = Math.round(parseFloat(f.peak_fee) * 100) || 0

    try {
      if (this.data.editing) {
        // 更新基本信息
        await api.put(`/api/admin/districts/${this.data.editing.id}`, {
          name: f.name.trim(),
          coverage: JSON.stringify(coverage),
          delivery_fee: deliveryFeeFen,
          delivery_range: parseInt(f.delivery_range) || 3,
          notice: f.notice || '',
          status: f.status,
        })
        // 保存高峰配送费设置（Query 参数）
        let peakStart = null, peakEnd = null
        if (f.peak_start && f.peak_start !== '') peakStart = parseInt(f.peak_start.split(':')[0])
        if (f.peak_end && f.peak_end !== '') peakEnd = parseInt(f.peak_end.split(':')[0])
        const qs = [
          `base_fee=${deliveryFeeFen}`,
          `peak_fee=${peakFeeFen}`,
          peakStart != null ? `peak_start_hour=${peakStart}` : '',
          peakEnd != null ? `peak_end_hour=${peakEnd}` : ''
        ].filter(Boolean).join('&')
        await api.put(`/api/admin/districts/${this.data.editing.id}/delivery-fee-settings?${qs}`)
        wx.showToast({ title: '分区已更新', icon: 'success' })
      } else {
        // 创建分区（Query 参数）
        const qs = [
          `name=${encodeURIComponent(f.name.trim())}`,
          `coverage=${encodeURIComponent(JSON.stringify(coverage))}`,
          `delivery_fee=${deliveryFeeFen}`,
          `delivery_range=${parseInt(f.delivery_range) || 3}`,
          `notice=${encodeURIComponent(f.notice || '')}`
        ].join('&')
        await api.post(`/api/admin/districts?${qs}`)
        wx.showToast({ title: '分区已创建', icon: 'success' })
      }
      this.resetForm()
      this.loadData()
    } catch (e) {}
  },
})
