const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    restaurantId: null,
    restaurant: null,
    cartItems: [],
    itemsTotal: 0,
    deliveryFee: 0,
    totalPrice: 0,
    address: null,
    remark: '',
  },

  onLoad(options) {
    const restaurantId = options.restaurant_id
    const cart = app.globalData.cart[restaurantId] || { items: [], restaurant_name: '' }
    const items = cart.items || []

    if (items.length === 0) {
      wx.showToast({ title: '购物车为空', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1000)
      return
    }

    this.setData({
      restaurantId,
      cartItems: items,
      itemsTotal: items.reduce((s, i) => s + i.price * i.quantity, 0),
    })

    this.loadRestaurant(restaurantId)
    this.loadDefaultAddress()
  },

  async loadRestaurant(id) {
    try {
      const res = await api.get(`/api/user/restaurants/${id}`)
      const deliveryFee = parseFloat(res.delivery_fee) || 0
      this.setData({
        restaurant: res,
        deliveryFee: deliveryFee,
        totalPrice: this.data.itemsTotal + deliveryFee,
      })
    } catch (e) { }
  },

  async loadDefaultAddress() {
    try {
      const addresses = await api.get('/api/user/addresses')
      const defaultAddr = addresses.find(a => a.is_default) || addresses[0] || null
      this.setData({ address: defaultAddr })
    } catch (e) { }
  },

  chooseAddress() {
    wx.chooseAddress({
      success: (res) => {
        // 微信原生地址选择器 (需用户授权)
        // 也可跳转到自定义地址页
      },
    })
    wx.navigateTo({ url: '/pages/address/address?select=1' })
  },

  onRemarkInput(e) {
    this.setData({ remark: e.detail.value })
  },

  async submitOrder() {
    if (!this.data.address) {
      wx.showToast({ title: '请选择收货地址', icon: 'none' })
      return
    }

    try {
      const order = await api.post('/api/user/orders', {
        restaurant_id: parseInt(this.data.restaurantId),
        address_id: this.data.address.id,
        items: this.data.cartItems.map(item => ({
          menu_item_id: item.menu_item_id,
          name: item.name,
          image: item.image,
          price: item.price,
          quantity: item.quantity,
        })),
        remark: this.data.remark,
      })

      // 清空该餐厅购物车
      const allCarts = app.globalData.cart
      delete allCarts[this.data.restaurantId]
      app.globalData.cart = allCarts
      wx.setStorageSync('cart', allCarts)

      // 弹出支付确认
      this.payOrder(order)
    } catch (e) { }
  },

  payOrder(order) {
    wx.showModal({
      title: '确认支付',
      content: `订单金额: ¥${order.total_price}\n\n(开发阶段为模拟支付)`,
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.post(`/api/user/orders/${order.id}/pay`)
            wx.showToast({ title: '支付成功', icon: 'success' })
            setTimeout(() => {
              wx.switchTab({ url: '/pages/orders/orders' })
            }, 800)
          } catch (e) { }
        } else {
          wx.showToast({ title: '订单已创建，请尽快支付', icon: 'none' })
          wx.switchTab({ url: '/pages/orders/orders' })
        }
      },
    })
  },
})
