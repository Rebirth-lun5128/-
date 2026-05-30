const api = require('../../utils/api')

Page({
  data: {
    storeTypes: [
      { label: '全部', value: '' },
      { label: '夜市摊位', value: 'stall' },
      { label: '家庭厨房', value: 'home_kitchen' },
      { label: '平台自营', value: 'self_operated' },
    ],
    // 品类图标
    categories: [
      { name: '烧烤', icon: '🍖', keyword: '烧烤', bg: '#FFF3E0' },
      { name: '面食', icon: '🍜', keyword: '面', bg: '#FFF9E6' },
      { name: '饮品', icon: '🥤', keyword: '饮品', bg: '#E3F2FD' },
      { name: '小吃', icon: '🍢', keyword: '小吃', bg: '#FFF5F0' },
      { name: '炒菜', icon: '🥘', keyword: '炒菜', bg: '#E8F5E9' },
      { name: '甜点', icon: '🍰', keyword: '甜点', bg: '#FCE4EC' },
      { name: '水果', icon: '🍉', keyword: '水果', bg: '#E8F5E9' },
      { name: '全部', icon: '🏪', keyword: '', bg: '#F3E5F5' },
    ],
    activeType: '',
    stores: [],
    featuredStores: [],
    page: 1,
    total: 0,
    loading: false,
    hasMore: true,
    keyword: '',
    districtNotice: '',
  },

  onLoad() {
    this.loadStores()
  },

  onShow() {
    if (!this.data.districtNotice) {
      this.loadDistrictNotice()
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, stores: [], hasMore: true })
    Promise.all([this.loadStores(), this.loadDistrictNotice()])
      .then(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadStores()
    }
  },

  async loadDistrictNotice() {
    try {
      const res = await api.get('/api/user/stores', { page: 1, page_size: 1 })
      if (res.items && res.items.length > 0) {
        const store = res.items[0]
        this.setData({ districtNotice: store.address || '社区美食配送' })
      }
    } catch (e) {}
  },

  async loadStores() {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const params = { page: this.data.page, page_size: 10 }
      if (this.data.activeType) params.store_type = this.data.activeType
      if (this.data.keyword) params.keyword = this.data.keyword

      const res = await api.get('/api/user/stores', params)
      const stores = this.data.page === 1 ? res.items : [...this.data.stores, ...res.items]

      // 热销推荐：取评分前 4 的店铺
      let featured = stores
      if (!this.data.keyword && !this.data.activeType) {
        featured = [...this.data.stores, ...stores]
          .sort((a, b) => (b.monthly_sales || 0) - (a.monthly_sales || 0))
          .slice(0, 6)
      }

      this.setData({
        stores,
        featuredStores: this.data.page === 1 ? res.items.sort((a, b) => (b.rating || 0) - (a.rating || 0)).slice(0, 6) : this.data.featuredStores,
        total: res.total,
        page: this.data.page + 1,
        hasMore: stores.length < res.total,
      })
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },

  onTypeTap(e) {
    const storeType = e.currentTarget.dataset.value
    if (storeType === this.data.activeType) return
    this.setData({ activeType: storeType, keyword: '', page: 1, stores: [], hasMore: true })
    this.loadStores()
  },

  onCategoryTap(e) {
    const kw = e.currentTarget.dataset.keyword
    this.setData({ keyword: kw, activeType: '', page: 1, stores: [], hasMore: true })
    this.loadStores()
  },

  onSearch(e) {
    this.setData({ keyword: e.detail.value, activeType: '', page: 1, stores: [], hasMore: true })
    this.loadStores()
  },

  onStoreTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/restaurant/restaurant?id=${id}` })
  },

  goToAll() {
    this.setData({ keyword: '', activeType: '', page: 1, stores: [], hasMore: true })
    this.loadStores()
  },

  goToCoupons() {
    wx.navigateTo({ url: '/pages/coupons/coupons' })
  },

  onScanTap() {
    wx.scanCode({
      success: (res) => {
        try {
          const data = JSON.parse(res.result)
          if (data.store_id) {
            wx.navigateTo({ url: `/pages/restaurant/restaurant?id=${data.store_id}` })
          }
        } catch {
          // 如果不是 JSON，尝试作为 URL 解析
          const match = res.result.match(/store_id[=:](\d+)/)
          if (match) {
            wx.navigateTo({ url: `/pages/restaurant/restaurant?id=${match[1]}` })
          } else {
            wx.showToast({ title: '无法识别的二维码', icon: 'none' })
          }
        }
      },
    })
  },

  onBannerTap(e) {
    const type = e.currentTarget.dataset.type
    switch (type) {
      case 'new_user':
        // 新人专享 → 优惠券页面
        wx.navigateTo({ url: '/pages/coupons/coupons' })
        break
      case 'flash_sale':
        // 限时特惠 → 搜索"特惠"或展示全部商家
        this.setData({ keyword: '', activeType: '', page: 1, stores: [], hasMore: true })
        this.loadStores()
        wx.pageScrollTo({ scrollTop: 300, duration: 300 })
        break
      case 'invite':
        // 邀请有礼 → 弹出分享引导
        wx.showModal({
          title: '邀请有礼',
          content: '点击右上角「···」分享给好友\n好友注册下单后，双方各得 ¥5 优惠券！',
          showCancel: false,
          confirmText: '知道了',
        })
        break
    }
  },
})
