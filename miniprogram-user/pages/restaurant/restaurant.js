const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    restaurant: null,
    categories: [],
    activeCategory: 0,
    cart: [],
    cartTotal: 0,
    cartCount: 0,
    showCartPopup: false,
    scrollToCategory: '',
  },

  onLoad(options) {
    const id = options.id
    this.setData({ restaurantId: id })
    this.loadRestaurant(id)
    this.loadCart()
  },

  async loadRestaurant(id) {
    try {
      const res = await api.get(`/api/user/stores/${id}`)
      this.setData({
        restaurant: res,
        categories: res.categories || [],
      })
    } catch (e) { }
  },

  loadCart() {
    const allCarts = app.globalData.cart
    const restaurantCart = allCarts[this.data.restaurantId] || { items: [], store_name: '' }
    const cart = restaurantCart.items || []
    const cartTotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0)
    const cartCount = cart.reduce((sum, item) => sum + item.quantity, 0)
    this.setData({ cart, cartTotal, cartCount })
  },

  onCategoryTap(e) {
    const index = e.currentTarget.dataset.index
    this.setData({ activeCategory: index, scrollToCategory: `category-${index}` })
  },

  addToCart(e) {
    const item = e.currentTarget.dataset.item
    const pid = item.product_id || item.id
    const allCarts = app.globalData.cart
    if (!allCarts[this.data.restaurantId]) {
      allCarts[this.data.restaurantId] = {
        items: [],
        store_name: this.data.restaurant ? this.data.restaurant.name : '',
        district_id: this.data.restaurant ? this.data.restaurant.district_id : null,
        combinable_districts: this.data.restaurant ? (this.data.restaurant.combinable_districts || []) : [],
      }
    }
    const cart = allCarts[this.data.restaurantId].items
    const existing = cart.find(c => c.product_id === pid)
    if (existing) {
      existing.quantity += 1
    } else {
      cart.push({
        product_id: pid,
        name: item.name,
        image: item.image,
        price: item.price,
        quantity: 1,
      })
    }
    this.saveCart(allCarts)
  },

  reduceFromCart(e) {
    const item = e.currentTarget.dataset.item
    const pid = item.product_id || item.id
    const allCarts = app.globalData.cart
    const cart = allCarts[this.data.restaurantId]?.items || []
    const idx = cart.findIndex(c => c.product_id === pid)
    if (idx >= 0) {
      cart[idx].quantity -= 1
      if (cart[idx].quantity <= 0) cart.splice(idx, 1)
      if (cart.length === 0) delete allCarts[this.data.restaurantId]
    }
    this.saveCart(allCarts)
  },

  saveCart(allCarts) {
    app.globalData.cart = allCarts
    wx.setStorageSync('cart', allCarts)
    this.loadCart()
  },

  clearCart() {
    const allCarts = app.globalData.cart
    delete allCarts[this.data.restaurantId]
    app.globalData.cart = allCarts
    wx.setStorageSync('cart', allCarts)
    this.loadCart()
    this.setData({ showCartPopup: false })
  },

  toggleCartPopup() {
    if (this.data.cartCount === 0) return
    this.setData({ showCartPopup: !this.data.showCartPopup })
  },

  goToCart() {
    wx.switchTab({ url: '/pages/cart/cart' })
  },

  goToConfirm() {
    if (!app.checkLogin()) return
    if (this.data.cartCount === 0) {
      wx.showToast({ title: '请先添加菜品', icon: 'none' })
      return
    }
    wx.navigateTo({ url: `/pages/order-confirm/order-confirm?store_id=${this.data.restaurantId}` })
  },
})
