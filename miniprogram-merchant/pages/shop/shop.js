const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    isRegister: false,
    form: {
      name: '',
      logo: '',
      banner: '',
      phone: '',
      address: '',
      category: '',
      stall_location: '',
      stall_photo: '',
      id_card_photo: '',
      min_price: '',
      delivery_fee: '',
      delivery_time: '30分钟',
      notice: '',
      status: 'closed',
    },
  },

  onLoad(options) {
    if (options.register === '1') {
      this.setData({ isRegister: true })
      wx.setNavigationBarTitle({ title: '店铺入驻' })
    }
  },

  onShow() {
    if (!app.checkLogin()) return
    if (!this.data.isRegister) this.loadShop()
  },

  async loadShop() {
    try {
      const shop = await api.get('/api/merchant/shop')
      this.setData({
        form: {
          name: shop.name || '',
          logo: shop.logo || '',
          banner: shop.banner || '',
          phone: shop.phone || '',
          address: shop.address || '',
          category: shop.category || '',
          stall_location: shop.stall_location || '',
          stall_photo: shop.stall_photo || '',
          id_card_photo: shop.id_card_photo || '',
          min_price: shop.min_price ? String(shop.min_price) : '',
          delivery_fee: shop.delivery_fee ? String(shop.delivery_fee) : '',
          delivery_time: shop.delivery_time || '30分钟',
          notice: shop.notice || '',
          status: shop.status || 'closed',
        },
      })
    } catch (e) { }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: e.detail.value })
  },

  onStatusChange(e) {
    this.setData({ 'form.status': e.detail.value })
  },

  async onSubmit() {
    const f = this.data.form
    const data = {
      name: f.name,
      logo: f.logo,
      banner: f.banner,
      phone: f.phone,
      address: f.address,
      category: f.category,
      stall_location: f.stall_location,
      stall_photo: f.stall_photo,
      id_card_photo: f.id_card_photo,
      min_price: f.min_price ? parseFloat(f.min_price) : 0,
      delivery_fee: f.delivery_fee ? parseFloat(f.delivery_fee) : 0,
      delivery_time: f.delivery_time,
      notice: f.notice,
      status: f.status,
    }

    try {
      if (this.data.isRegister) {
        await api.post('/api/merchant/shop/register', data)
        wx.showToast({ title: '入驻申请已提交', icon: 'success' })
        setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 800)
      } else {
        await api.put('/api/merchant/shop', data)
        wx.showToast({ title: '保存成功', icon: 'success' })
      }
    } catch (e) { }
  },
})
