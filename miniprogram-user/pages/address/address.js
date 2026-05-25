const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    addresses: [],
    selectMode: false, // 是否为选择地址模式
  },

  onLoad(options) {
    if (options.select === '1') {
      this.setData({ selectMode: true })
    }
  },

  onShow() {
    if (!app.globalData.token) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
    this.loadAddresses()
  },

  async loadAddresses() {
    try {
      const addresses = await api.get('/api/user/addresses')
      this.setData({ addresses })
    } catch (e) { }
  },

  onSelect(e) {
    if (!this.data.selectMode) return
    const addr = e.currentTarget.dataset.addr
    // 将选中的地址传回上一页
    const pages = getCurrentPages()
    const prevPage = pages[pages.length - 2]
    if (prevPage) {
      prevPage.setData({ address: addr })
    }
    wx.navigateBack()
  },

  onEdit(e) {
    const id = e.currentTarget.dataset.id
    wx.navigateTo({ url: `/pages/address-form/address-form?id=${id}` })
  },

  onAdd() {
    wx.navigateTo({ url: '/pages/address-form/address-form' })
  },

  async onDelete(e) {
    const id = e.currentTarget.dataset.id
    const res = await new Promise(r => wx.showModal({ title: '确认删除', content: '确定删除该地址吗？', success: r }))
    if (!res.confirm) return
    try {
      await api.del(`/api/user/addresses/${id}`)
      wx.showToast({ title: '已删除', icon: 'success' })
      this.loadAddresses()
    } catch (e) { }
  },
})
