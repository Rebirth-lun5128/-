const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    dashboard: null,
    settlement: null,
    commissionRateText: '12.0',
    showWithdraw: false,
    withdrawAmount: '',
  },

  onShow() {
    if (!app.checkLogin()) return
    this.loadData()
  },

  async loadData() {
    try {
      const [dash, settle] = await Promise.all([
        api.get('/api/merchant/shop/dashboard'),
        api.get('/api/merchant/shop/settlement'),
      ])
      const rate = Number(dash.commission_rate)
      const commissionRateText = (Number.isFinite(rate) ? rate * 100 : 12).toFixed(1)
      this.setData({ dashboard: dash, settlement: settle, commissionRateText })
    } catch (e) { }
  },

  onWithdrawTap() {
    this.setData({ showWithdraw: true, withdrawAmount: '' })
  },

  onWithdrawCancel() {
    this.setData({ showWithdraw: false, withdrawAmount: '' })
  },

  onAmountInput(e) {
    this.setData({ withdrawAmount: e.detail.value })
  },

  async onWithdrawConfirm() {
    const amount = parseFloat(this.data.withdrawAmount)
    if (!amount || amount <= 0) {
      wx.showToast({ title: '请输入有效金额', icon: 'none' })
      return
    }
    try {
      const res = await api.post('/api/merchant/shop/withdraw', { amount })
      wx.showToast({ title: res.message || '申请已提交', icon: 'success' })
      this.setData({ showWithdraw: false, withdrawAmount: '' })
      this.loadData()
    } catch (e) { }
  },
})
