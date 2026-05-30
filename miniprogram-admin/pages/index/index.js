const api = require('../../utils/api')
const { getWsBase } = require('../../utils/config')
const app = getApp()

Page({
  data: {
    dashboard: null,
    chartStats: [],
    maxCount: 0,
    visits: { today: 0, yesterday: 0, total: 0 },
    roleTitle: '管理员',
    isSuperAdmin: true,
    newOrderDot: false,

    // 配送模式
    deliveryMode: 'inactive',   // inactive | standby | active | busy
    activeOrder: null,
    pendingOrders: [],
    pendingTotal: 0,
    deliveryWallet: { balance: 0, total_orders: 0, today_income: 0 },
    // 提现
    showWithdrawForm: false,
    withdrawAmount: '',
    withdrawing: false,
    // 配送记录 & 提现记录
    showDeliveryOrders: false,
    deliveryOrders: [],
    deliveryOrdersTotal: 0,
    showWithdrawals: false,
    withdrawals: [],
    withdrawalsTotal: 0,
  },

  onShow() {
    if (!app.checkLogin()) return
    // 兜底：如果 globalData 还没恢复（onLaunch 未完成），直接从 storage 读
    const role = app.globalData.role || wx.getStorageSync('admin_role') || ''
    this.setData({
      roleTitle: role === 'district_admin' ? '分区管理员' : '超级管理员',
      isSuperAdmin: role === 'super_admin',
    })
    this.loadDashboard()
    this.loadStats()
    this.loadVisits()
    this.trackVisit()
    this.loadDeliveryStatus()
    this.connectWs()
  },

  onHide() {
    this.closeWs()
  },

  onUnload() {
    this.closeWs()
  },

  // ---- WebSocket ----
  connectWs() {
    const token = app.globalData.token
    if (!token) return
    // 用 app.globalData 防重复连接
    if (app.globalData._wsTask && app.globalData._wsOpen) return
    const wsUrl = `${getWsBase()}/ws?token=${encodeURIComponent(token)}`
    const task = wx.connectSocket({ url: wsUrl })
    app.globalData._wsTask = task
    task.onOpen(() => { app.globalData._wsOpen = true })
    task.onMessage((res) => {
      try {
        const data = JSON.parse(res.data)
        if (data.event === 'new_order') {
          this.setData({ newOrderDot: true })
          // 如果配送模式开启，自动刷新待接单列表
          if (this.data.deliveryMode === 'active') {
            this.loadPendingOrders()
          }
        }
      } catch (_) {}
    })
    task.onClose(() => { app.globalData._wsOpen = false })
    task.onError(() => { app.globalData._wsOpen = false })
  },

  closeWs() {
    if (app.globalData._wsTask) {
      try { app.globalData._wsTask.close({}) } catch (_) {}
      app.globalData._wsOpen = false
    }
  },

  async loadDashboard() {
    try {
      const res = await api.get('/api/admin/dashboard')
      this.setData({ dashboard: res })
    } catch (e) {}
  },

  async loadStats() {
    try {
      const res = await api.get('/api/admin/orders/stats', { days: 7 })
      const max = Math.max(...res.map(s => s.count), 1)
      this.setData({ chartStats: res, maxCount: max })
    } catch (e) {}
  },

  async loadVisits() {
    try {
      const res = await api.get('/api/admin/visits/stats', { days: 7 })
      this.setData({ visits: { today: res.today || 0, yesterday: res.yesterday || 0, total: res.total || 0 } })
    } catch (e) {}
  },

  trackVisit() {
    api.post('/api/admin/visits/track').catch(() => {})
  },

  // ====== 配送模式 ======
  async loadDeliveryStatus() {
    try {
      const res = await api.get('/api/admin/delivery/status')
      this.setData({
        deliveryMode: res.mode || 'inactive',
        activeOrder: res.active_order || null,
        deliveryWallet: { balance: 0, total_orders: 0, today_income: 0 },
      })
      if (res.mode === 'active' || res.mode === 'busy') {
        this.loadPendingOrders()
        this.loadDeliveryWallet()
        this.loadMyDeliveryOrders()
        this.loadMyWithdrawals()
      }
    } catch (e) {}
  },

  async loadPendingOrders() {
    try {
      const res = await api.get('/api/admin/delivery/pending')
      this.setData({
        pendingOrders: res.items || [],
        pendingTotal: res.total || 0,
      })
    } catch (e) {}
  },

  async loadDeliveryWallet() {
    try {
      const res = await api.get('/api/admin/delivery/wallet')
      this.setData({ deliveryWallet: res })
    } catch (e) {}
  },

  async toggleDelivery(e) {
    const enable = e.detail.value
    try {
      await api.put(`/api/admin/delivery/toggle?enable=${enable}`)
      wx.showToast({ title: enable ? '配送模式已开启' : '配送模式已关闭', icon: 'success' })
      this.loadDeliveryStatus()
    } catch (e) {}
  },

  async acceptOrder(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认接单',
      content: '接单后请尽快取餐配送',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.put(`/api/admin/delivery/orders/${id}/accept`)
          wx.showToast({ title: '已接单', icon: 'success' })
          this.loadDeliveryStatus()
        } catch (e) {}
      },
    })
  },

  async deliverOrder() {
    const order = this.data.activeOrder
    if (!order) return
    wx.showModal({
      title: '确认送达',
      content: '请确认已将所有商品送到用户手中',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.put(`/api/admin/delivery/orders/${order.id}/deliver`)
          wx.showToast({ title: '已送达', icon: 'success' })
          this.loadDeliveryStatus()
        } catch (e) {}
      },
    })
  },

  // === 导航（非 tab 页用 navigateTo，tab 页用 switchTab + globalData） ===
  goCustomers() {
    wx.navigateTo({ url: '/pages/customers/customers' })
  },

  goStores() {
    app.globalData.storeFilter = null
    wx.switchTab({ url: '/pages/stores/stores' })
  },

  goStoresVerify() {
    app.globalData.storeFilter = 'unverified'
    wx.switchTab({ url: '/pages/stores/stores' })
  },

  goOrders() {
    this.setData({ newOrderDot: false })
    app.globalData.orderFilter = null
    wx.switchTab({ url: '/pages/orders/orders' })
  },

  goOrdersPending() {
    app.globalData.orderFilter = { tab: 'orders', status: 'pending' }
    wx.switchTab({ url: '/pages/orders/orders' })
  },

  goOrdersModifications() {
    app.globalData.orderFilter = { tab: 'modifications', status: '' }
    wx.switchTab({ url: '/pages/orders/orders' })
  },

  goSettlements() {
    wx.navigateTo({ url: '/pages/settlements/settlements' })
  },

  // ---- 提现 ----
  showWithdraw() {
    this.setData({ showWithdrawForm: true, withdrawAmount: '' })
  },
  closeWithdraw() {
    this.setData({ showWithdrawForm: false })
  },
  onWithdrawInput(e) {
    this.setData({ withdrawAmount: e.detail.value })
  },
  async submitWithdraw() {
    const amt = parseFloat(this.data.withdrawAmount)
    if (!amt || amt < 10) return
    this.setData({ withdrawing: true })
    try {
      const res = await api.post('/api/admin/delivery/withdraw', { amount: amt })
      wx.showToast({ title: res.message || '已提交', icon: 'success' })
      this.setData({ showWithdrawForm: false })
      this.loadDeliveryWallet()
    } catch (e) {} finally {
      this.setData({ withdrawing: false })
    }
  },

  // ---- 配送记录 ----
  toggleDeliveryOrders() {
    this.setData({ showDeliveryOrders: !this.data.showDeliveryOrders })
  },

  async loadMyDeliveryOrders() {
    try {
      const res = await api.get('/api/admin/delivery/my-orders', { page_size: 5 })
      this.setData({
        deliveryOrders: res.items || [],
        deliveryOrdersTotal: res.total || 0,
      })
    } catch (e) {}
  },

  // ---- 提现记录 ----
  toggleWithdrawals() {
    this.setData({ showWithdrawals: !this.data.showWithdrawals })
  },

  async loadMyWithdrawals() {
    try {
      const res = await api.get('/api/admin/delivery/withdrawals', { page_size: 5 })
      this.setData({
        withdrawals: res.items || [],
        withdrawalsTotal: res.total || 0,
      })
    } catch (e) {}
  },

  // ---- 退出登录 ----
  handleLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出当前账号吗？',
      success: (res) => {
        if (res.confirm) {
          app.logout()
        }
      },
    })
  },
})
