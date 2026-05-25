const api = require('../../utils/api')

Page({
  data: {
    isEdit: false,
    form: {
      id: null,
      contact_name: '',
      contact_phone: '',
      gender: 1,
      province: '',
      city: '',
      district: '',
      detail: '',
      label: '',
      is_default: 0,
    },
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ isEdit: true })
      this.loadAddress(options.id)
    }
  },

  async loadAddress(id) {
    try {
      const addresses = await api.get('/api/user/addresses')
      const addr = addresses.find(a => a.id == id)
      if (addr) {
        this.setData({
          form: { ...addr },
        })
      }
    } catch (e) { }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onGenderChange(e) {
    this.setData({ 'form.gender': parseInt(e.detail.value) })
  },

  async onSubmit() {
    const f = this.data.form
    if (!f.contact_name || !f.contact_phone || !f.detail) {
      wx.showToast({ title: '请填写必填项', icon: 'none' })
      return
    }

    try {
      if (this.data.isEdit) {
        await api.put(`/api/user/addresses/${f.id}`, f)
      } else {
        await api.post('/api/user/addresses', f)
      }
      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 500)
    } catch (e) { }
  },
})
