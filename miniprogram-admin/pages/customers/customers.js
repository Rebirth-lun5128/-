const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    users: [],
    total: 0,
    keyword: '',
    loading: false,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadData()
  },

  onSearchInput(e) {
    this.setData({ keyword: e.detail.value })
    clearTimeout(this._searchTimer)
    this._searchTimer = setTimeout(() => this.loadData(), 300)
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const params = {}
      if (this.data.keyword) params.keyword = this.data.keyword
      const res = await api.get('/api/admin/customers', params)
      this.setData({ users: res.items || [], total: res.total || 0 })
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },
})
