const api = require('../../utils/api')

Page({
  data: {
    isEdit: false,
    categories: [],
    form: {
      id: null,
      category_id: null,
      name: '',
      image: '',
      price: '',
      original_price: '',
      description: '',
    },
  },

  onLoad(options) {
    this.loadCategories()
    if (options.id) {
      this.setData({ isEdit: true, itemId: options.id })
      this.loadItem(options.id)
    } else if (options.category_id) {
      this.setData({ 'form.category_id': parseInt(options.category_id) || null })
    }
  },

  async loadCategories() {
    try {
      const cats = await api.get('/api/merchant/menu/categories')
      this.setData({ categories: cats })
    } catch (e) { }
  },

  async loadItem(id) {
    try {
      const items = await api.get('/api/merchant/menu/items')
      const item = items.find(i => i.id == id)
      if (item) {
        this.setData({
          form: {
            id: item.id,
            category_id: item.category_id,
            name: item.name,
            image: item.image,
            price: String(item.price),
            original_price: item.original_price ? String(item.original_price) : '',
            description: item.description,
          },
        })
      }
    } catch (e) { }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onCategoryChange(e) {
    this.setData({ 'form.category_id': parseInt(e.detail.value) || null })
  },

  async onSubmit() {
    const f = this.data.form
    if (!f.name || !f.price) {
      wx.showToast({ title: '请填写名称和价格', icon: 'none' })
      return
    }

    const data = {
      name: f.name,
      image: f.image,
      price: parseFloat(f.price),
      original_price: f.original_price ? parseFloat(f.original_price) : null,
      description: f.description,
      category_id: f.category_id,
    }

    try {
      if (this.data.isEdit) {
        await api.put(`/api/merchant/menu/items/${f.id}`, data)
      } else {
        await api.post('/api/merchant/menu/items', data)
      }
      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 500)
    } catch (e) { }
  },
})
