const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    wallet: null,
    settlements: [],
    withdrawing: false,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadWallet()
    this.loadSettlements()
  },

  async loadWallet() {
    try {
      const res = await api.get('/api/rider/orders/wallet')
      this.setData({ wallet: res })
    } catch (e) { }
  },

  async loadSettlements() {
    try {
      const res = await api.get('/api/rider/orders/settlements')
      this.setData({ settlements: res.items || [] })
    } catch (e) { }
  },

  doWithdraw() {
    const balance = this.data.wallet.balance
    if (balance <= 0) return

    wx.showModal({
      title: '申请结算',
      content: `当前可结算余额 ¥${balance}\n确认提交结算申请？\n管理员审核后将线下打款`,
      confirmText: '确认申请',
      success: async (res) => {
        if (!res.confirm) return
        this.setData({ withdrawing: true })
        try {
          const result = await api.post('/api/rider/orders/withdraw', { amount: balance })
          wx.showToast({ title: result.message || '申请已提交', icon: 'success' })
          this.loadWallet()
        } catch (e) { } finally {
          this.setData({ withdrawing: false })
        }
      },
    })
  },
})
