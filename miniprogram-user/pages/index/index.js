const api = require('../../utils/api')

Page({
  data: {
    categories: ['全部', '中餐', '西餐', '快餐', '小吃', '饮品', '甜品'],
    activeCategory: '全部',
    restaurants: [],
    page: 1,
    total: 0,
    loading: false,
    hasMore: true,
    keyword: '',
  },

  onLoad() {
    this.loadRestaurants()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, restaurants: [], hasMore: true })
    this.loadRestaurants().then(() => wx.stopPullDownRefresh())
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadRestaurants()
    }
  },

  async loadRestaurants() {
    if (this.data.loading) return
    this.setData({ loading: true })

    try {
      const params = { page: this.data.page, page_size: 10 }
      if (this.data.activeCategory !== '全部') params.category = this.data.activeCategory
      if (this.data.keyword) params.keyword = this.data.keyword

      const res = await api.get('/api/user/restaurants', params)
      const restaurants = this.data.page === 1 ? res.items : [...this.data.restaurants, ...res.items]

      this.setData({
        restaurants,
        total: res.total,
        page: this.data.page + 1,
        hasMore: restaurants.length < res.total,
      })
    } catch (e) {
      // handled in api.js
    } finally {
      this.setData({ loading: false })
    }
  },

  onCategoryTap(e) {
    const category = e.currentTarget.dataset.category
    if (category === this.data.activeCategory) return
    this.setData({ activeCategory: category, page: 1, restaurants: [], hasMore: true })
    this.loadRestaurants()
  },

  onSearch(e) {
    this.setData({ keyword: e.detail.value, page: 1, restaurants: [], hasMore: true })
    this.loadRestaurants()
  },

  onRestaurantTap(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/restaurant/restaurant?id=${id}` })
  },
})
