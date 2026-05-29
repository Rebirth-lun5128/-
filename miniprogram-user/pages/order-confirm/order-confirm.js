const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    storeIds: [],         // 所有店铺ID
    storeGroups: [],      // [{store_id, store_name, items, subtotal}]
    itemsTotal: 0,
    deliveryFee: 0,
    deliveryFeeOriginal: 0,
    deliveryFeeDiscount: 0,
    deliveryFeeDetail: '', // 配送费说明文字
    couponDiscount: 0,
    totalPrice: 0,
    address: null,
    remark: '',
    coupons: [],
    selectedCoupon: null,
    selectedCouponId: null,
    showCouponPopup: false,
    isCombined: false,    // 是否合并下单
  },

  onLoad(options) {
    const storeIds = options.store_ids
      ? options.store_ids.split(',').map(Number)
      : [parseInt(options.store_id)]

    const isCombined = storeIds.length > 1
    const groups = []
    let total = 0

    for (const sid of storeIds) {
      const cart = app.globalData.cart[sid]
      if (!cart || !cart.items || cart.items.length === 0) continue
      const subtotal = cart.items.reduce((s, i) => s + i.price * i.quantity, 0)
      groups.push({
        store_id: sid,
        store_name: cart.store_name || '未知店铺',
        items: cart.items,
        subtotal: subtotal.toFixed(2),
      })
      total += subtotal
    }

    if (groups.length === 0) {
      wx.showToast({ title: '购物车为空', icon: 'none' })
      setTimeout(() => wx.navigateBack(), 1000)
      return
    }

    this.setData({
      storeIds,
      storeGroups: groups,
      isCombined,
      itemsTotal: total,
      cartItems: groups[0].items, // 兼容旧模板
      restaurantId: groups[0].store_id, // 兼容
    })

    if (isCombined) {
      this.loadCombinedDeliveryFee()
    } else {
      this.loadRestaurant(storeIds[0])
    }
    this.loadDefaultAddress()
    this.loadCoupons()
  },

  async loadRestaurant(id) {
    try {
      const res = await api.get(`/api/user/stores/${id}`)
      const deliveryFee = parseFloat(res.delivery_fee) || 0
      this.setData({ restaurant: res, deliveryFee })
      this.calcTotal()
    } catch (e) {}
  },

  async loadCombinedDeliveryFee() {
    // 对于合并订单，先简单使用第一家的配送费占位
    // 实际配送费由后端计算
    try {
      const res = await api.get(`/api/user/stores/${this.data.storeIds[0]}`)
      this.setData({
        deliveryFee: parseFloat(res.delivery_fee) || 0,
        restaurant: res,
      })
      this.calcTotal()
    } catch (e) {
      this.calcTotal()
    }
  },

  async loadDefaultAddress() {
    try {
      const addresses = await api.get('/api/user/addresses')
      const defaultAddr = addresses.find(a => a.is_default) || addresses[0] || null
      this.setData({ address: defaultAddr })
    } catch (e) {}
  },

  async loadCoupons() {
    try {
      const res = await api.get('/api/user/coupons/my')
      const valid = res.filter(c => c.status === 'unused')
      this.setData({ coupons: valid })
    } catch (e) {}
  },

  calcTotal() {
    const deliveryFee = this.data.deliveryFee || 0
    const discount = this.data.couponDiscount || 0
    const total = Math.max(0, this.data.itemsTotal + deliveryFee - discount)
    this.setData({ totalPrice: total })
  },

  showCouponPicker() {
    this.setData({ showCouponPopup: true })
  },

  hideCouponPicker() {
    this.setData({ showCouponPopup: false })
  },

  noop() {},

  onSelectCoupon(e) {
    const item = e.currentTarget.dataset.item
    if (item.coupon_type === 'full_reduction' && this.data.itemsTotal < item.condition_amount) {
      return
    }
    this.setData({
      selectedCoupon: item,
      selectedCouponId: item.id,
      couponDiscount: parseFloat(item.discount_amount) || 0,
      showCouponPopup: false,
    })
    this.calcTotal()
  },

  onClearCoupon() {
    this.setData({
      selectedCoupon: null,
      selectedCouponId: null,
      couponDiscount: 0,
      showCouponPopup: false,
    })
    this.calcTotal()
  },

  chooseAddress() {
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

    if (this.data.isCombined) {
      await this.submitCombinedOrder()
    } else {
      await this.submitSingleOrder()
    }
  },

  async submitCombinedOrder() {
    const body = {
      address_id: this.data.address.id,
      sub_orders: this.data.storeGroups.map(g => ({
        store_id: g.store_id,
        items: g.items.map(item => ({
          product_id: item.product_id,
          name: item.name,
          image: item.image || '',
          price: item.price,
          quantity: item.quantity,
        })),
      })),
      remark: this.data.remark,
    }
    if (this.data.selectedCouponId) {
      body.user_coupon_id = this.data.selectedCouponId
    }

    try {
      const order = await api.post('/api/user/orders', body)

      // 清空所有相关店铺购物车
      const allCarts = app.globalData.cart
      for (const sid of this.data.storeIds) {
        delete allCarts[sid]
      }
      app.globalData.cart = allCarts
      wx.setStorageSync('cart', allCarts)

      this.payOrder(order)
    } catch (e) {}
  },

  async submitSingleOrder() {
    try {
      const body = {
        address_id: this.data.address.id,
        sub_orders: [{
          store_id: this.data.storeIds[0],
          items: this.data.storeGroups[0].items.map(item => ({
            product_id: item.product_id,
            name: item.name,
            image: item.image || '',
            price: item.price,
            quantity: item.quantity,
          })),
        }],
        remark: this.data.remark,
      }
      if (this.data.selectedCouponId) {
        body.user_coupon_id = this.data.selectedCouponId
      }

      const order = await api.post('/api/user/orders', body)

      const allCarts = app.globalData.cart
      delete allCarts[this.data.storeIds[0]]
      app.globalData.cart = allCarts
      wx.setStorageSync('cart', allCarts)

      this.payOrder(order)
    } catch (e) {}
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
          } catch (e) {}
        } else {
          wx.showToast({ title: '订单已创建，请尽快支付', icon: 'none' })
          wx.switchTab({ url: '/pages/orders/orders' })
        }
      },
    })
  },
})
