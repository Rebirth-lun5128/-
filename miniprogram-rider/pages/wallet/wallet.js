const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    wallet: null,
    withdrawing: false,
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

  doWithdraw() {
    const balance = this.data.wallet.balance
    if (balance <= 0) return

    wx.showModal({
      title: '提现到微信零钱',
      content: `当前可提现余额 ¥${balance}\n确认全部提现到微信零钱？`,
      confirmText: '确认提现',
      success: async (res) => {
        if (!res.confirm) return
        this.setData({ withdrawing: true })
        try {
          const result = await api.post('/api/rider/orders/withdraw', { amount: balance })
          wx.showToast({ title: result.message || '提现成功', icon: 'success' })
          this.loadWallet()
        } catch (e) { } finally {
          this.setData({ withdrawing: false })
        }
      },
    })
  },
})
