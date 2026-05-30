const api = require('../../utils/api')

Page({
  data: {
    order: null,
    statusMap: {
      pending_accept: '待接单',
      preparing: '备货中',
      ready: '待取餐',
      delivering: '配送中',
      completed: '已完成',
      cancelled: '已取消',
    },
  },

  onLoad(options) {
    this.loadOrder(options.id)
  },

  async loadOrder(id) {
    try {
      const res = await api.get(`/api/rider/orders/${id}`)
      this.setData({ order: res })
    } catch (e) { }
  },

  takePhoto() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['camera'],
      success: (res) => {
        const filePath = res.tempFilePaths[0]
        wx.showLoading({ title: '上传中...' })
        // 先用通用上传，再存到订单
        wx.uploadFile({
          url: require('../../utils/config').getApiBase() + '/api/common/upload',
          filePath,
          name: 'file',
          header: { 'Authorization': 'Bearer ' + (wx.getStorageSync('token') || '') },
          success: (uploadRes) => {
            wx.hideLoading()
            try {
              const data = JSON.parse(uploadRes.data)
              if (data.url) {
                this.saveDeliveryPhoto(data.url)
              }
            } catch { wx.showToast({ title: '上传失败', icon: 'none' }) }
          },
          fail: () => { wx.hideLoading(); wx.showToast({ title: '上传失败', icon: 'none' }) },
        })
      },
    })
  },

  async saveDeliveryPhoto(url) {
    try {
      await api.put(`/api/rider/orders/${this.data.order.id}/delivery-photo`, { photo_url: url })
      wx.showToast({ title: '已上传', icon: 'success' })
      this.loadOrder(this.data.order.id)
    } catch { }
  },

  openNavigation() {
    const addr = this.data.order.address_snapshot
    if (!addr) {
      wx.showToast({ title: '暂无收货地址坐标', icon: 'none' })
      return
    }
    const lat = parseFloat(addr.lat)
    const lng = parseFloat(addr.lng)
    if (!lat || !lng) {
      wx.showToast({ title: '收货地址无坐标，请电话联系用户', icon: 'none' })
      return
    }
    wx.openLocation({
      latitude: lat,
      longitude: lng,
      name: addr.detail || addr.address || '收货地址',
      address: `${addr.province || ''}${addr.city || ''}${addr.district || ''}${addr.detail || ''}`,
      scale: 16,
    })
  },
})
