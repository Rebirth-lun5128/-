const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    categories: [],
    activeCategory: 0,
    allItems: [],
    filteredItems: [],
    showEditModal: false,
    editModalTitle: '',
    editModalValue: '',
    editModalMode: 'add',
    editingCatId: 0,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadData()
  },

  async loadData() {
    try {
      const cats = await api.get('/api/merchant/menu/categories')
      const items = await api.get('/api/merchant/menu/items')
      this.setData({ categories: cats, allItems: items }, () => this.updateFilteredItems())
    } catch (e) { }
  },

  onCategoryTap(e) {
    this.setData({ activeCategory: e.currentTarget.dataset.index }, () => this.updateFilteredItems())
  },

  onCategoryMore(e) {
    const index = e.currentTarget.dataset.index
    const cat = this.data.categories[index]
    if (!cat) return
    const total = this.data.categories.length
    const itemList = ['编辑名称', '删除分类']
    if (index > 0) itemList.push('上移')
    if (index < total - 1) itemList.push('下移')

    wx.showActionSheet({
      itemList,
      success: (res) => {
        const action = itemList[res.tapIndex]
        if (action === '编辑名称') this.editCategory(cat, index)
        else if (action === '删除分类') this.deleteCategory(cat, index)
        else if (action === '上移') this.moveCategory(index, -1)
        else if (action === '下移') this.moveCategory(index, 1)
      },
    })
  },

  onCategoryLongPress(e) {
    const index = e.currentTarget.dataset.index
    const cat = this.data.categories[index]
    if (!cat) return
    const total = this.data.categories.length
    const itemList = ['编辑名称', '删除分类']
    if (index > 0) itemList.push('上移')
    if (index < total - 1) itemList.push('下移')

    wx.showActionSheet({
      itemList,
      success: (res) => {
        const action = itemList[res.tapIndex]
        if (action === '编辑名称') this.editCategory(cat, index)
        else if (action === '删除分类') this.deleteCategory(cat, index)
        else if (action === '上移') this.moveCategory(index, -1)
        else if (action === '下移') this.moveCategory(index, 1)
      },
    })
  },

  editCategory(cat, index) {
    setTimeout(() => {
      this.setData({
        showEditModal: true,
        editModalMode: 'edit',
        editModalTitle: '编辑分类名称',
        editModalValue: cat.name,
        editingCatId: cat.id,
      })
    }, 300)
  },

  onEditModalInput(e) {
    this.setData({ editModalValue: e.detail.value })
  },

  onEditModalCancel() {
    this.setData({ showEditModal: false, editModalValue: '' })
  },

  async onEditModalConfirm() {
    const { editModalMode, editModalValue, editingCatId } = this.data
    const name = editModalValue.trim()
    if (!name) {
      wx.showToast({ title: '请输入名称', icon: 'none' })
      return
    }
    this.setData({ showEditModal: false, editModalValue: '' })
    try {
      if (editModalMode === 'edit') {
        await api.put(`/api/merchant/menu/categories/${editingCatId}`, { name, sort_order: 0 })
      } else {
        await api.post('/api/merchant/menu/categories', { name, sort_order: 0 })
      }
      wx.showToast({ title: editModalMode === 'edit' ? '已更新' : '已添加', icon: 'success' })
      this.loadData()
    } catch (e) { }
  },

  deleteCategory(cat, index) {
    wx.showModal({
      title: '删除分类',
      content: `确定删除「${cat.name}」吗？该分类下的商品不会被删除。`,
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.del(`/api/merchant/menu/categories/${cat.id}`)
            wx.showToast({ title: '已删除', icon: 'success' })
            if (this.data.activeCategory >= this.data.categories.length - 1) {
              this.setData({ activeCategory: Math.max(0, this.data.activeCategory - 1) })
            }
            this.loadData()
          } catch (e) { }
        }
      },
    })
  },

  async moveCategory(index, direction) {
    const cats = [...this.data.categories]
    const newIndex = index + direction
    if (newIndex < 0 || newIndex >= cats.length) return
    ;[cats[index], cats[newIndex]] = [cats[newIndex], cats[index]]
    this.setData({ categories: cats, activeCategory: newIndex }, () => this.updateFilteredItems())
    try {
      await api.put('/api/merchant/menu/categories/sort', cats.map(c => c.id))
    } catch (e) {
      this.loadData()
    }
  },

  updateFilteredItems() {
    const { categories, activeCategory, allItems } = this.data
    if (!categories.length) {
      this.setData({ filteredItems: allItems })
      return
    }
    const catId = categories[activeCategory]?.id
    this.setData({ filteredItems: allItems.filter((i) => i.category_id === catId) })
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
    setTimeout(() => {
      this.setData({
        showEditModal: true,
        editModalMode: 'add',
        editModalTitle: '添加分类',
        editModalValue: '',
        editingCatId: 0,
      })
    }, 300)
  },
})
