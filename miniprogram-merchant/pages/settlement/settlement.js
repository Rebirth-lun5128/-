const app = getApp()

Page({
  data: {
    dashboard: null,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadData()
  },

  async loadData() {
    const api = require('../../utils/api')
    try {
      const res = await api.get('/api/merchant/shop/dashboard')
      this.setData({ dashboard: res })
    } catch (e) { }
  },
})
