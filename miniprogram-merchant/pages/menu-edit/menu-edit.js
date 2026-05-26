const api = require('../../utils/api')
const { getApiBase } = require('../../utils/config')

Page({
  data: {
    isEdit: false,
    categories: [],
    selectedCatName: '',
    stockUnlimited: true,
    limitUnlimited: true,
    form: {
      id: null,
      category_id: null,
      name: '',
      image: '',
      price: '',
      original_price: '',
      description: '',
      stock: '-1',
      limit_per_order: '0',
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
      if (this.data.form.category_id) {
        const idx = cats.findIndex(c => c.id === this.data.form.category_id)
        if (idx >= 0) this.setData({ selectedCatName: cats[idx].name })
      }
    } catch (e) { }
  },

  async loadItem(id) {
    try {
      const items = await api.get('/api/merchant/menu/items')
      const item = items.find(i => i.id == id)
      if (item) {
        const cats = this.data.categories
        const catIdx = cats.findIndex(c => c.id === item.category_id)
        const stock = item.stock ?? -1
        const limit = item.limit_per_order ?? 0
        this.setData({
          selectedCatName: catIdx >= 0 ? cats[catIdx].name : '',
          stockUnlimited: stock === -1,
          limitUnlimited: limit === 0,
          form: {
            id: item.id,
            category_id: item.category_id,
            name: item.name,
            image: item.image || '',
            price: String(item.price),
            original_price: item.original_price ? String(item.original_price) : '',
            description: item.description || '',
            stock: stock === -1 ? '-1' : String(stock),
            limit_per_order: limit === 0 ? '0' : String(limit),
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
    const idx = parseInt(e.detail.value)
    const cat = this.data.categories[idx]
    this.setData({
      'form.category_id': cat ? cat.id : null,
      selectedCatName: cat ? cat.name : '',
    })
  },

  onStockToggle(e) {
    const unlimited = e.detail.value
    this.setData({
      stockUnlimited: unlimited,
      'form.stock': unlimited ? '-1' : '',
    })
  },

  onStockPreset(e) {
    const val = e.currentTarget.dataset.val
    this.setData({ 'form.stock': val })
  },

  onStockInput(e) {
    this.setData({ 'form.stock': e.detail.value })
  },

  onLimitToggle(e) {
    const unlimited = e.detail.value
    this.setData({
      limitUnlimited: unlimited,
      'form.limit_per_order': unlimited ? '0' : '',
    })
  },

  onChooseImage() {
    const token = wx.getStorageSync('merchant_token')
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempPath = res.tempFilePaths[0]
        wx.showLoading({ title: '上传中...' })
        wx.uploadFile({
          url: getApiBase() + '/api/common/upload',
          filePath: tempPath,
          name: 'file',
          header: { 'Authorization': `Bearer ${token}` },
          success: (uploadRes) => {
            const data = JSON.parse(uploadRes.data)
            if (data.url) {
              this.setData({ 'form.image': getApiBase() + data.url })
            }
          },
          fail: () => {
            wx.showToast({ title: '上传失败', icon: 'none' })
          },
          complete: () => {
            wx.hideLoading()
          },
        })
      },
    })
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
      stock: this.data.stockUnlimited ? -1 : (parseInt(f.stock) || -1),
      limit_per_order: this.data.limitUnlimited ? 0 : (parseInt(f.limit_per_order) || 0),
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
