const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    userInfo: null,
    orderCount: 0,
    pendingCount: 0,
    deliveringCount: 0,
    couponCount: 0,
  },

  onShow() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
    const cached = app.globalData.userInfo || wx.getStorageSync('userInfo') || { nickname: '食客' }
    this.setData({ userInfo: cached })
    this.refreshUser()
    this.loadStats()
  },

  async refreshUser() {
    try {
      const user = await api.get('/api/common/auth/me', null, { silent: true })
      app.globalData.userInfo = user
      wx.setStorageSync('userInfo', user)
      this.setData({ userInfo: user })
    } catch (e) {}
  },

  async loadStats() {
    const silent = { silent: true }
    const stats = await Promise.all([
      api.get('/api/user/orders', { page: 1, page_size: 1, status: '' }, silent).catch(() => ({ total: 0 })),
      api.get('/api/user/orders', { page: 1, page_size: 1, status: 'pending_pay' }, silent).catch(() => ({ total: 0 })),
      api.get('/api/user/orders', { page: 1, page_size: 1, status: 'delivering' }, silent).catch(() => ({ total: 0 })),
      api.get('/api/user/coupons/my', null, silent).catch(() => []),
    ])
    this.setData({
      orderCount: stats[0].total || 0,
      pendingCount: stats[1].total || 0,
      deliveringCount: stats[2].total || 0,
      couponCount: Array.isArray(stats[3]) ? stats[3].filter(c => c.status === 'unused').length : 0,
    })
  },

  goToOrders(e) {
    const status = e.currentTarget.dataset.status || ''
    wx.switchTab({ url: '/pages/orders/orders' })
    // 状态筛选通过全局事件传递
    if (status) {
      app.globalData.orderFilter = status
    }
  },

  goToCoupons() {
    wx.navigateTo({ url: '/pages/coupons/coupons' })
  },

  goToAddress() {
    wx.navigateTo({ url: '/pages/address/address' })
  },

  goToFavorites() {
    wx.showToast({ title: '收藏功能开发中', icon: 'none' })
  },

  goToCart() {
    wx.switchTab({ url: '/pages/index/index' })
    // 触发跳转到购物车
    setTimeout(() => {
      wx.navigateTo({ url: '/pages/cart/cart' })
    }, 200)
  },

  editProfile() {
    wx.navigateTo({ url: '/pages/profile-edit/profile-edit' })
  },

  contactSupport() {
    wx.showModal({
      title: '联系客服',
      content: '客服电话：138-0000-0000\n工作时间：17:00 - 00:00',
      showCancel: true,
    })
  },

  showAbout() {
    wx.showModal({
      title: '关于夜市外卖',
      content: '社区夜市外卖平台\n为社区提供便捷的美食外卖服务\n\n版本：1.0.0',
      showCancel: false,
    })
  },

  logout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出吗？',
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('userInfo')
          app.globalData.token = ''
          app.globalData.userInfo = null
          wx.navigateTo({ url: '/pages/login/login' })
        }
      },
    })
  },

  deleteAccount() {
    wx.showModal({
      title: '注销账号',
      content: '注销后您的账户将被禁用，手机号将被释放。\n\n如有未完成订单请先处理完毕。\n\n确定要注销吗？',
      confirmText: '确认注销',
      confirmColor: '#E53935',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.delete('/api/common/auth/account')
            wx.showToast({ title: '账号已注销', icon: 'success' })
            wx.removeStorageSync('token')
            wx.removeStorageSync('userInfo')
            app.globalData.token = ''
            app.globalData.userInfo = null
            setTimeout(() => wx.navigateTo({ url: '/pages/login/login' }), 1000)
          } catch (e) {}
        }
      },
    })
  },
})
