const app = getApp()

Page({
  data: {
    restaurants: [], // 按店铺分组的购物车 [{ store_id, store_name, items, subtotal }]
    isEmpty: true,
  },

  onShow() {
    this.loadCart()
  },

  loadCart() {
    const allCarts = app.globalData.cart || {}
    const entries = Object.entries(allCarts)
    const restaurants = entries.map(([restaurantId, cart]) => {
      const items = cart.items || []
      const subtotal = items.reduce((s, i) => s + i.price * i.quantity, 0)
      return {
        store_id: parseInt(restaurantId),
        store_name: cart.store_name || '未知店铺',
        items,
        subtotal: subtotal.toFixed(2),
      }
    }).filter(r => r.items.length > 0)

    const totalPrice = restaurants.reduce((s, r) => s + parseFloat(r.subtotal), 0).toFixed(2)

    this.setData({
      restaurants,
      totalPrice,
      isEmpty: restaurants.length === 0,
    })
  },

  /** 增加数量 */
  addItem(e) {
    const { rid, itemId } = e.currentTarget.dataset
    const allCarts = app.globalData.cart
    const cart = allCarts[rid]
    if (!cart) return
    const item = cart.items.find(i => i.product_id === itemId)
    if (item) item.quantity += 1
    this.syncCart(allCarts)
  },

  /** 减少数量 */
  reduceItem(e) {
    const { rid, itemId } = e.currentTarget.dataset
    const allCarts = app.globalData.cart
    const cart = allCarts[rid]
    if (!cart) return
    const idx = cart.items.findIndex(i => i.product_id === itemId)
    if (idx >= 0) {
      cart.items[idx].quantity -= 1
      if (cart.items[idx].quantity <= 0) cart.items.splice(idx, 1)
      if (cart.items.length === 0) delete allCarts[rid]
    }
    this.syncCart(allCarts)
  },

  /** 删除菜品 */
  removeItem(e) {
    const { rid, itemId } = e.currentTarget.dataset
    wx.showModal({
      title: '移除菜品',
      content: '确定从购物车移除该菜品吗？',
      success: (res) => {
        if (!res.confirm) return
        const allCarts = app.globalData.cart
        const cart = allCarts[rid]
        if (!cart) return
        cart.items = cart.items.filter(i => i.product_id !== itemId)
        if (cart.items.length === 0) delete allCarts[rid]
        this.syncCart(allCarts)
      },
    })
  },

  /** 清空某餐厅购物车 */
  clearRestaurant(e) {
    const rid = e.currentTarget.dataset.rid
    wx.showModal({
      title: '清空购物车',
      content: '确定清空该餐厅的所有菜品吗？',
      success: (res) => {
        if (!res.confirm) return
        const allCarts = app.globalData.cart
        delete allCarts[rid]
        this.syncCart(allCarts)
      },
    })
  },

  syncCart(allCarts) {
    app.globalData.cart = allCarts
    wx.setStorageSync('cart', allCarts)
    this.loadCart()
  },

  /** 去结算（单店） */
  goCheckout(e) {
    if (!app.checkLogin()) return
    const rid = e.currentTarget.dataset.rid
    wx.navigateTo({ url: `/pages/order-confirm/order-confirm?store_id=${rid}` })
  },

  /** 合并结算（多店铺） */
  goCombinedCheckout() {
    if (!app.checkLogin()) return
    const storeIds = this.data.restaurants.map(r => r.store_id).join(',')
    wx.navigateTo({ url: `/pages/order-confirm/order-confirm?store_ids=${storeIds}` })
  },

  /** 返回首页继续点餐 */
  goHome() {
    wx.switchTab({ url: '/pages/index/index' })
  },
})
