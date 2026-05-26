const api = require('../../utils/api')

Page({
  data: {
    order: null,
    statusMap: {
      pending_accept: '待接单',
      preparing: '备货中',
      ready: '待取餐',
      delivering: '配送中',
      completed: '已完成',
      cancelled: '已取消',
    },
  },

  onLoad(options) {
    this.loadOrder(options.id)
  },

  async loadOrder(id) {
    try {
      const res = await api.get(`/api/rider/orders/${id}`)
      this.setData({ order: res })
    } catch (e) { }
  },
})
