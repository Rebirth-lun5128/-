const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    categories: [],
    activeCategory: 0,
    allItems: [],
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadData()
  },

  async loadData() {
    try {
      const cats = await api.get('/api/merchant/menu/categories')
      const items = await api.get('/api/merchant/menu/items')
      this.setData({ categories: cats, allItems: items })
    } catch (e) { }
  },

  onCategoryTap(e) {
    this.setData({ activeCategory: e.currentTarget.dataset.index })
  },

  getFilteredItems() {
    const cats = this.data.categories
    const items = this.data.allItems
    if (cats.length === 0) return items
    const catId = cats[this.data.activeCategory]?.id
    return items.filter(i => i.category_id === catId)
  },

  addItem() {
    const catId = this.data.categories[this.data.activeCategory]?.id
    wx.navigateTo({ url: `/pages/menu-edit/menu-edit?category_id=${catId || ''}` })
  },

  editItem(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/menu-edit/menu-edit?id=${id}` })
  },

  async toggleStatus(e) {
    const { id, status } = e.currentTarget.dataset
    try {
      await api.put(`/api/merchant/menu/items/${id}/status?status=${status === 1 ? 0 : 1}`)
      wx.showToast({ title: status === 1 ? '已下架' : '已上架', icon: 'success' })
      this.loadData()
    } catch (e) { }
  },

  addCategory() {
    wx.showModal({
      title: '添加分类',
      editable: true,
      placeholderText: '请输入分类名称',
      success: async (res) => {
        if (res.confirm && res.content) {
          try {
            await api.post('/api/merchant/menu/categories', { name: res.content, sort_order: 0 })
            wx.showToast({ title: '已添加', icon: 'success' })
            this.loadData()
          } catch (e) { }
        }
      },
    })
  },
})
