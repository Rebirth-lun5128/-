const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    wallet: null,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadWallet()
  },

  async loadWallet() {
    try {
      const res = await api.get('/api/rider/orders/wallet')
      this.setData({ wallet: res })
    } catch (e) { }
  },
})
