const api = require('../../utils/api')

Page({
  data: { order: null },

  onLoad(options) {
    // 从骑手端获取订单详情
    this.loadOrder(options.id)
  },

  async loadOrder(id) {
    try {
      const res = await api.get('/api/rider/orders/my')
      const order = (res.items || []).find(o => o.id == id)
      if (order) {
        this.setData({ order })
      }
    } catch (e) { }
  },
})
