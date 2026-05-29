const api = require('../../utils/api')
const { getApiBase } = require('../../utils/config')

Page({
  data: {
    storeId: null,
    storeName: '',
    categories: [],
    products: [],
    activeCategoryId: null,  // null = 全部

    // 商品弹窗
    showProdDialog: false,
    dialogTitle: '',
    editingProd: null,
    catPickerLabel: '未分类',
    prodForm: {
      name: '', image: '', price: 0.01, original_price: null,
      description: '', stock: -1, sort_order: 0, category_id: null,
      is_recommended: 0
    },

    // 分类弹窗
    showCatDialog: false,
    catFormName: '',
    editingCatId: null,
  },

  onLoad(options) {
    const storeId = options.store_id
    const storeName = decodeURIComponent(options.store_name || '')
    this.setData({ storeId, storeName })
    this.loadCategories()
    this.loadProducts()
  },

  // ====== 分类 ======
  async loadCategories() {
    try {
      const res = await api.get('/api/admin/categories', { store_id: this.data.storeId })
      this.setData({ categories: Array.isArray(res) ? res : [] })
    } catch (e) { }
  },

  onCatTap(e) {
    const id = e.currentTarget.dataset.id
    this.setData({ activeCategoryId: id || null })
    this.loadProducts()
  },

  openCatAdd() {
    this.setData({ showCatDialog: true, catFormName: '', editingCatId: null })
  },

  openCatEdit(e) {
    const id = e.currentTarget.dataset.id
    const name = e.currentTarget.dataset.name
    this.setData({ showCatDialog: true, catFormName: name, editingCatId: id })
  },

  onCatNameInput(e) {
    this.setData({ catFormName: e.detail.value })
  },

  async saveCategory() {
    const name = this.data.catFormName.trim()
    if (!name) return
    try {
      if (this.data.editingCatId) {
        await api.put(`/api/admin/categories/${this.data.editingCatId}`, { name, sort_order: 0 })
      } else {
        await api.post(`/api/admin/categories?store_id=${this.data.storeId}`, { name, sort_order: 0 })
      }
      wx.showToast({ title: '已保存', icon: 'success' })
      this.setData({ showCatDialog: false })
      this.loadCategories()
    } catch (e) { }
  },

  async deleteCategory(e) {
    const id = e.currentTarget.dataset.id
    const res = await new Promise(r => wx.showModal({
      title: '删除分类',
      content: '该分类下的商品将变为未分类，确认删除？',
      success: r,
    }))
    if (!res.confirm) return
    try {
      await api.delete(`/api/admin/categories/${id}`)
      wx.showToast({ title: '已删除', icon: 'success' })
      if (this.data.activeCategoryId === id) this.setData({ activeCategoryId: null })
      this.loadCategories()
      this.loadProducts()
    } catch (e) { }
  },

  // ====== 商品 ======
  async loadProducts() {
    try {
      const params = { store_id: this.data.storeId }
      if (this.data.activeCategoryId) params.category_id = this.data.activeCategoryId
      const res = await api.get('/api/admin/products', params)
      this.setData({ products: Array.isArray(res) ? res : [] })
    } catch (e) { }
  },

  async toggleStatus(e) {
    const { id, status } = e.currentTarget.dataset
    const newStatus = status === 1 ? 0 : 1
    try {
      await api.put(`/api/admin/products/${id}/status?status=${newStatus}`)
      wx.showToast({ title: newStatus === 1 ? '已上架' : '已下架', icon: 'success' })
      this.loadProducts()
    } catch (e) { }
  },

  async deleteProduct(e) {
    const id = e.currentTarget.dataset.id
    const res = await new Promise(r => wx.showModal({
      title: '确认删除', content: '删除后不可恢复',
      success: r,
    }))
    if (!res.confirm) return
    try {
      await api.delete(`/api/admin/products/${id}`)
      wx.showToast({ title: '已删除', icon: 'success' })
      this.loadProducts()
    } catch (e) { }
  },

  // ====== 商品弹窗 ======
  openProdAdd() {
    this.setData({
      showProdDialog: true,
      dialogTitle: '添加商品',
      editingProd: null,
      prodForm: {
        name: '', image: '', price: 0.01, original_price: null,
        description: '', stock: -1, sort_order: 0,
        category_id: this.data.activeCategoryId,
        is_recommended: 0
      }
    })
    this.updateCatPickerLabel()
  },

  openProdEdit(e) {
    const prod = this.data.products.find(p => p.id == e.currentTarget.dataset.id)
    if (!prod) return
    this.setData({
      showProdDialog: true,
      dialogTitle: '编辑商品',
      editingProd: prod.id,
      prodForm: {
        name: prod.name, image: prod.image, price: prod.price,
        original_price: prod.original_price, description: prod.description || '',
        stock: prod.stock, sort_order: prod.sort_order,
        category_id: prod.category_id, is_recommended: prod.is_recommended
      }
    })
    this.updateCatPickerLabel()
  },

  onProdFieldInput(e) {
    const { field } = e.currentTarget.dataset
    this.setData({ [`prodForm.${field}`]: e.detail.value })
  },

  onProdNumInput(e) {
    const { field } = e.currentTarget.dataset
    const val = parseFloat(e.detail.value)
    this.setData({ [`prodForm.${field}`]: isNaN(val) ? 0 : val })
  },

  onCatPicker(e) {
    const idx = e.detail.value
    const cat = this.data.categories[idx]
    if (cat) {
      this.setData({ 'prodForm.category_id': cat.id, catPickerLabel: cat.name })
    }
  },

  updateCatPickerLabel() {
    const cat = this.data.categories.find(c => c.id === this.data.prodForm.category_id)
    this.setData({ catPickerLabel: cat ? cat.name : '未分类' })
  },

  onSwitchRec(e) {
    this.setData({ 'prodForm.is_recommended': e.detail.value ? 1 : 0 })
  },

  closeProdDialog() { this.setData({ showProdDialog: false }) },
  closeCatDialog() { this.setData({ showCatDialog: false }) },

  onChooseImage() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      success: (res) => {
        wx.showLoading({ title: '上传中' })
        wx.uploadFile({
          url: getApiBase() + '/api/common/upload',
          filePath: res.tempFilePaths[0],
          name: 'file',
          header: { Authorization: 'Bearer ' + wx.getStorageSync('admin_token') },
          success: (uploadRes) => {
            try {
              const data = JSON.parse(uploadRes.data)
              if (data.url) {
                this.setData({ 'prodForm.image': data.url })
                wx.showToast({ title: '上传成功', icon: 'success' })
              }
            } catch (e) { }
          },
          fail: () => wx.showToast({ title: '上传失败', icon: 'none' }),
          complete: () => wx.hideLoading(),
        })
      },
    })
  },

  async saveProduct() {
    const f = this.data.prodForm
    if (!f.name.trim()) {
      wx.showToast({ title: '请输入商品名称', icon: 'none' })
      return
    }
    try {
      if (this.data.editingProd) {
        await api.put(`/api/admin/products/${this.data.editingProd}`, f)
      } else {
        await api.post(`/api/admin/products?store_id=${this.data.storeId}`, f)
      }
      wx.showToast({ title: '已保存', icon: 'success' })
      this.setData({ showProdDialog: false })
      this.loadProducts()
    } catch (e) { }
  },
})
