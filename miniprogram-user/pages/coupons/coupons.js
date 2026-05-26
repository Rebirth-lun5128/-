const api = require('../../utils/api')

Page({
  data: {
    activeTab: 'available',
    availableList: [],
    myList: [],
  },

  onShow() {
    if (this.data.activeTab === 'available') {
      this.loadAvailable()
    } else {
      this.loadMy()
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    if (tab === this.data.activeTab) return
    this.setData({ activeTab: tab })
    if (tab === 'available') this.loadAvailable()
    else this.loadMy()
  },

  async loadAvailable() {
    try {
      const res = await api.get('/api/user/coupons/available')
      this.setData({ availableList: res })
    } catch (e) { }
  },

  async loadMy() {
    try {
      const res = await api.get('/api/user/coupons/my')
      this.setData({ myList: res })
    } catch (e) { }
  },

  async claimCoupon(e) {
    const id = e.currentTarget.dataset.id
    try {
      await api.post(`/api/user/coupons/${id}/claim`)
      wx.showToast({ title: '领取成功', icon: 'success' })
      this.loadAvailable()
    } catch (e) { }
  },
})
