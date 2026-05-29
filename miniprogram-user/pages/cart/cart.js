const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    districts: [],
    totalStores: 0,
    totalItems: 0,
    isEmpty: true,
    // 勾选模式
    selectedIds: [],       // 已勾选的 store_id 数组
    selectedCount: 0,
    selectedTotal: 0,
    crossDistrict: false,  // 是否跨区
  },

  onShow() {
    this.loadCart()
  },

  async loadCart() {
    const allCarts = app.globalData.cart || {}

    let districtNames = {}
    try {
      const list = await api.get('/api/user/stores/districts/list')
      list.forEach(d => { districtNames[d.id] = d.name })
    } catch (e) {}

    const districtMap = {}
    let totalStores = 0
    let totalItems = 0
    const allStoreIds = []

    Object.entries(allCarts).forEach(([storeId, cart]) => {
      if (!cart.items || cart.items.length === 0) return
      const store_id = parseInt(storeId)
      const district_id = cart.district_id || 0
      const items = cart.items
      const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0)

      if (!districtMap[district_id]) {
        districtMap[district_id] = {
          district_id,
          district_name: districtNames[district_id] || `分区 #${district_id}`,
          stores: [],
          subtotal: 0,
        }
      }

      districtMap[district_id].stores.push({
        store_id,
        store_name: cart.store_name || '未知店铺',
        items,
        subtotal: subtotal.toFixed(2),
        combinable_districts: cart.combinable_districts || [],
      })
      districtMap[district_id].subtotal += subtotal
      totalStores++
      totalItems += items.reduce((s, i) => s + i.quantity, 0)
      allStoreIds.push(store_id)
    })

    const districts = Object.values(districtMap).sort((a, b) => a.district_id - b.district_id)

    // 保留已有勾选，新店默认勾选
    const prevSelected = new Set(this.data.selectedIds)
    const isFirstLoad = this.data.selectedIds.length === 0
    const selectedIds = isFirstLoad
      ? [...allStoreIds]  // 首次加载全选
      : allStoreIds.filter(id => prevSelected.has(id))  // 保留已有勾选

    // 为每个店铺写入 checked 字段，WXML 无法调用 indexOf
    const selectedSet = new Set(selectedIds)
    districts.forEach(d => {
      d.stores.forEach(s => { s.checked = selectedSet.has(s.store_id) })
    })

    this.setData({
      districts,
      totalStores,
      totalItems,
      isEmpty: districts.length === 0,
      selectedIds,
    })
    this.updateSelection(allCarts)
  },

  // ---- 勾选 / 取消 ----
  toggleStore(e) {
    const sid = e.currentTarget.dataset.sid
    let selectedIds = [...this.data.selectedIds]
    const idx = selectedIds.indexOf(sid)
    if (idx > -1) {
      selectedIds.splice(idx, 1)
    } else {
      selectedIds.push(sid)
    }
    this.setData({ selectedIds })

    // 同步更新 districts 里的 checked 状态
    const selectedSet = new Set(selectedIds)
    const districts = this.data.districts
    districts.forEach(d => {
      d.stores.forEach(s => { s.checked = selectedSet.has(s.store_id) })
    })
    this.setData({ districts })

    this.updateSelection(app.globalData.cart)
  },

  updateSelection(allCarts) {
    const selectedIds = this.data.selectedIds
    const selectedSet = new Set(selectedIds)
    let selectedTotal = 0
    let selectedCount = 0
    const districts = new Set()

    for (const sid of selectedIds) {
      const cart = allCarts[sid]
      if (!cart || !cart.items) continue
      selectedCount++
      districts.add(cart.district_id || 0)
      selectedTotal += cart.items.reduce((s, i) => s + i.price * i.quantity, 0)
    }

    const crossDistrict = districts.size > 1

    this.setData({
      selectedCount,
      selectedTotal: selectedTotal.toFixed(2),
      crossDistrict,
    })
  },

  // ---- 加减删 ----
  addItem(e) {
    const { rid, itemId } = e.currentTarget.dataset
    const pid = parseInt(itemId)
    const allCarts = app.globalData.cart
    const cart = allCarts[rid]
    if (!cart) return
    const item = cart.items.find(i => i.product_id === pid)
    if (item) item.quantity += 1
    this.sync(allCarts)
  },

  reduceItem(e) {
    const { rid, itemId } = e.currentTarget.dataset
    const pid = parseInt(itemId)
    const allCarts = app.globalData.cart
    const cart = allCarts[rid]
    if (!cart) return
    const idx = cart.items.findIndex(i => i.product_id === pid)
    if (idx >= 0) {
      cart.items[idx].quantity -= 1
      if (cart.items[idx].quantity <= 0) cart.items.splice(idx, 1)
      if (cart.items.length === 0) delete allCarts[rid]
    }
    this.sync(allCarts)
  },

  removeItem(e) {
    const { rid, itemId } = e.currentTarget.dataset
    const pid = parseInt(itemId)
    wx.showModal({
      title: '移除菜品',
      content: '确定从购物车移除该菜品吗？',
      success: (res) => {
        if (!res.confirm) return
        const allCarts = app.globalData.cart
        const cart = allCarts[rid]
        if (!cart) return
        cart.items = cart.items.filter(i => i.product_id !== pid)
        if (cart.items.length === 0) delete allCarts[rid]
        this.sync(allCarts)
      },
    })
  },

  clearStore(e) {
    const rid = e.currentTarget.dataset.rid
    wx.showModal({
      title: '清空店铺',
      content: '确定清空该店铺的所有菜品吗？',
      success: (res) => {
        if (!res.confirm) return
        const allCarts = app.globalData.cart
        delete allCarts[rid]
        this.sync(allCarts)
      },
    })
  },

  sync(allCarts) {
    app.globalData.cart = allCarts
    wx.setStorageSync('cart', allCarts)
    this.loadCart()
  },

  // ---- 统一结算 ----
  submitSelected() {
    if (!app.checkLogin()) return
    if (this.data.crossDistrict) {
      wx.showToast({ title: '跨区店铺需分开结算', icon: 'none' })
      return
    }
    if (this.data.selectedIds.length === 0) {
      wx.showToast({ title: '请选择要结算的店铺', icon: 'none' })
      return
    }
    const ids = this.data.selectedIds.join(',')
    wx.navigateTo({ url: `/pages/order-confirm/order-confirm?store_ids=${ids}` })
  },

  goHome() {
    wx.switchTab({ url: '/pages/index/index' })
  },
})
