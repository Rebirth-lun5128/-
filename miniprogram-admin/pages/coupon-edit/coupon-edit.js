const api = require('../../utils/api')

Page({
  data: {
    isEdit: false,
    couponId: null,
    types: ['满减券', '立减券', '新用户券'],
    typeKeys: ['full_reduction', 'direct_discount', 'new_user'],
    typeIndex: 0,
    form: {
      name: '',
      discount_amount: '',
      condition_amount: '',
      total_count: '0',
      start_time: '',
      end_time: '',
    },
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ isEdit: true, couponId: options.id })
      this.loadCoupon(options.id)
    }
  },

  async loadCoupon(id) {
    try {
      const res = await api.get('/api/admin/coupons')
      const list = Array.isArray(res) ? res : (res.items || [])
      const c = list.find(r => r.id == id)
      if (!c) return
      const ti = this.data.typeKeys.indexOf(c.coupon_type)
      this.setData({
        typeIndex: ti >= 0 ? ti : 0,
        form: {
          name: c.name || '',
          discount_amount: String(c.discount_amount || ''),
          condition_amount: String(c.condition_amount || ''),
          total_count: String(c.total_count || 0),
          start_time: c.start_time ? c.start_time.slice(0, 10) : '',
          end_time: c.end_time ? c.end_time.slice(0, 10) : '',
        },
      })
    } catch (e) {}
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onTypeChange(e) {
    this.setData({ typeIndex: parseInt(e.detail.value) })
  },

  async onSubmit() {
    const f = this.data.form
    if (!f.name.trim() || !f.discount_amount) {
      wx.showToast({ title: '请填写名称和减免金额', icon: 'none' })
      return
    }
    const params = {
      name: f.name.trim(),
      coupon_type: this.data.typeKeys[this.data.typeIndex],
      discount_amount: parseFloat(f.discount_amount),
      condition_amount: f.condition_amount ? parseFloat(f.condition_amount) : 0,
      total_count: parseInt(f.total_count) || 0,
      start_time: f.start_time || null,
      end_time: f.end_time || null,
    }

    try {
      if (this.data.isEdit) {
        await api.put(`/api/admin/coupons/${this.data.couponId}`, params)
      } else {
        await api.post('/api/admin/coupons', params)
      }
      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 600)
    } catch (e) {}
  },
})
