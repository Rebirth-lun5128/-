const api = require('../../utils/api')
const { getApiBase } = require('../../utils/config')
const app = getApp()

Page({
  data: {
    isRegister: false,
    storeTypes: ['夜市摊位', '家庭厨房', '平台自营'],
    storeTypeKeys: ['stall', 'home_kitchen', 'self_operated'],
    storeTypeIndex: 0,
    form: {
      store_type: 'stall',
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
      const typeIdx = this.data.storeTypeKeys.indexOf(shop.store_type || 'stall')
      this.setData({
        storeTypeIndex: typeIdx >= 0 ? typeIdx : 0,
        form: {
          store_type: shop.store_type || 'stall',
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

  onChooseImage(e) {
    const field = e.currentTarget.dataset.field
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
              this.setData({ [`form.${field}`]: getApiBase() + data.url })
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

  onStoreTypeChange(e) {
    const idx = parseInt(e.detail.value)
    this.setData({
      storeTypeIndex: idx,
      'form.store_type': this.data.storeTypeKeys[idx],
    })
  },

  setStatus(e) {
    this.setData({ 'form.status': e.currentTarget.dataset.status })
  },

  async onSubmit() {
    const f = this.data.form
    const data = {
      store_type: f.store_type,
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
      delivery_time: f.delivery_time,
      notice: f.notice,
      status: f.status,
    }

    try {
      if (this.data.isRegister) {
        await api.post('/api/merchant/shop/register', data)
        wx.showToast({ title: '入驻申请已提交，等待核验', icon: 'success' })
        setTimeout(() => wx.switchTab({ url: '/pages/index/index' }), 800)
      } else {
        await api.put('/api/merchant/shop', data)
        wx.showToast({ title: '保存成功', icon: 'success' })
      }
    } catch (e) { }
  },

  onLogout() {
    wx.showModal({
      title: '退出登录',
      content: '退出后需重新登录，确定退出吗？',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('merchant_token')
          wx.removeStorageSync('merchant_info')
          app.globalData.token = ''
          app.globalData.shopInfo = null
          wx.reLaunch({ url: '/pages/login/login' })
        }
      }
    })
  },
})
