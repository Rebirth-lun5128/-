const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    districts: [],
    editing: null,
    form: {
      name: '',
      coverage: '',
      delivery_fee: 0,
      delivery_range: 3,
      notice: '',
    },
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadData()
  },

  async loadData() {
    try {
      const res = await api.get('/api/admin/districts')
      this.setData({ districts: Array.isArray(res) ? res : (res.items || []) })
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
        delivery_fee: d.delivery_fee || 0,
        delivery_range: d.delivery_range || 3,
        notice: d.notice || '',
      },
    })
    wx.pageScrollTo({ scrollTop: 9999 })
  },

  resetForm() {
    this.setData({
      editing: null,
      form: { name: '', coverage: '', delivery_fee: 0, delivery_range: 3, notice: '' },
    })
  },

  async saveDistrict() {
    const f = this.data.form
    if (!f.name.trim()) {
      wx.showToast({ title: '请输入分区名称', icon: 'none' })
      return
    }
    const coverage = f.coverage ? f.coverage.split(/[,，、\s]+/).filter(Boolean) : []
    try {
      if (this.data.editing) {
        await api.put(`/api/admin/districts/${this.data.editing.id}`, {
          name: f.name.trim(),
          coverage: JSON.stringify(coverage),
          delivery_fee: parseInt(f.delivery_fee) || 0,
          delivery_range: parseFloat(f.delivery_range) || 3,
          notice: f.notice || '',
        })
        wx.showToast({ title: '分区已更新', icon: 'success' })
      } else {
        await api.post('/api/admin/districts', {
          name: f.name.trim(),
          coverage: JSON.stringify(coverage),
          delivery_fee: parseInt(f.delivery_fee) || 0,
          delivery_range: parseFloat(f.delivery_range) || 3,
          notice: f.notice || '',
        })
        wx.showToast({ title: '分区已创建', icon: 'success' })
      }
      this.resetForm()
      this.loadData()
    } catch (e) {}
  },
})
