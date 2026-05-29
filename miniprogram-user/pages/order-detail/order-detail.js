const api = require('../../utils/api')
const ws = require('../../utils/websocket')
const util = require('../../utils/util')

Page({
  data: {
    order: null,
    timeline: [],
    reviewScore: 5,
    reviewTags: [],
    reviewContent: '',
    riderLat: null,
    riderLng: null,
    mapMarkers: [],
  },

  onLoad(options) {
    this.orderId = options.id
    this.loadOrder(options.id)
  },

  onUnload() {
    ws.close()
  },

  connectWS() {
    ws.connect()
    // 监听订单状态变化
    ws.on('*', (data) => {
      const orderId = data.order && (data.order.id || data.order.order_id)
      if (!orderId || orderId !== this.orderId) return
      if (data.event === 'rider_location') {
        const rlat = data.lat || (data.order && data.order.lat)
        const rlng = data.lng || (data.order && data.order.lng)
        if (rlat && rlng) {
          this.setData({
            riderLat: rlat,
            riderLng: rlng,
            mapMarkers: [
              { id: 1, latitude: rlat, longitude: rlng, width: 32, height: 32, callout: { content: '骑手', fontSize: 12, borderRadius: 8, padding: 4, display: 'ALWAYS' } },
              ...(this.data.destLat && this.data.destLng ? [{ id: 2, latitude: this.data.destLat, longitude: this.data.destLng, width: 28, height: 28, callout: { content: '收货点', fontSize: 12, borderRadius: 8, padding: 4, display: 'ALWAYS' } }] : []),
            ],
          })
        }
        return
      }
      // 其他状态变更 — 重新拉取订单
      this.loadOrder(this.orderId)
    })
  },

  async loadOrder(id) {
    try {
      const order = await api.get(`/api/user/orders/${id}`)
      const addr = order.address_snapshot
      const destLat = addr.lat || null
      const destLng = addr.lng || null

      // 新架构：sub_orders 存在时使用子单
      const hasSubOrders = order.sub_orders && order.sub_orders.length > 0
      const firstSub = hasSubOrders ? order.sub_orders[0] : null

      this.setData({
        order: {
          ...order,
          statusText: util.getOrderStatusText(order.status),
          statusColor: util.getOrderStatusColor(order.status),
        },
        subOrders: order.sub_orders || [],
        hasSubOrders,
        timeline: hasSubOrders && firstSub ? (firstSub.timeline || []) : (order.timeline || []),
        storeName: hasSubOrders ? order.sub_orders.map(s => s.store_name || s.store_name_snapshot).join('、') : (order.store_name || ''),
        storeNameList: hasSubOrders ? order.sub_orders.map(s => s.store_name || s.store_name_snapshot) : [],
        items: hasSubOrders ? [] : (order.items || []),
        destLat: destLat,
        destLng: destLng,
      })

      const liveStatuses = ['pending', 'pending_accept', 'preparing', 'ready', 'delivering']
      if (liveStatuses.includes(order.status)) {
        this.connectWS()
      }

      // 配送中时尝试获取骑手位置
      if (order.status === 'delivering') {
        try {
          const loc = await api.get(`/api/user/orders/${id}/rider-location`)
          if (loc.lat && loc.lng) {
            this.setData({
              riderLat: loc.lat,
              riderLng: loc.lng,
              mapMarkers: [
                { id: 1, latitude: loc.lat, longitude: loc.lng, width: 32, height: 32, callout: { content: '骑手', fontSize: 12, borderRadius: 8, padding: 4, display: 'ALWAYS' } },
                ...(destLat && destLng ? [{ id: 2, latitude: destLat, longitude: destLng, width: 28, height: 28, callout: { content: '收货点', fontSize: 12, borderRadius: 8, padding: 4, display: 'ALWAYS' } }] : []),
              ],
            })
          }
        } catch (e) { }
      }
    } catch (e) { }
  },

  setScore(e) {
    this.setData({ reviewScore: parseInt(e.currentTarget.dataset.score) })
  },

  toggleTag(e) {
    const tag = e.currentTarget.dataset.tag
    let tags = this.data.reviewTags
    const idx = tags.indexOf(tag)
    if (idx >= 0) {
      tags = tags.filter(t => t !== tag)
    } else {
      tags = [...tags, tag]
    }
    this.setData({ reviewTags: tags })
  },

  onReviewInput(e) {
    this.setData({ reviewContent: e.detail.value })
  },

  async submitReview(e) {
    const subId = e ? e.currentTarget.dataset.subId : null
    // 如果有子单，评价第一个未评价的子单
    let targetSubId = subId
    if (!targetSubId && this.data.subOrders && this.data.subOrders.length > 0) {
      const unreviewed = this.data.subOrders.find(s => !s.review && s.status === 'completed')
      targetSubId = unreviewed ? unreviewed.id : null
    }
    if (!targetSubId) {
      wx.showToast({ title: '无可评价的子单', icon: 'none' })
      return
    }
    try {
      await api.post(`/api/user/orders/sub/${targetSubId}/review`, {
        score: this.data.reviewScore,
        content: this.data.reviewContent,
        tags: this.data.reviewTags,
      })
      wx.showToast({ title: '评价成功', icon: 'success' })
      this.loadOrder(this.data.order.id)
    } catch (e) { }
  },

  payOrder() {
    wx.showModal({
      title: '确认支付',
      content: `订单金额: ¥${this.data.order.total_price}`,
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.post(`/api/user/orders/${this.data.order.id}/pay`)
            wx.showToast({ title: '支付成功', icon: 'success' })
            this.loadOrder(this.data.order.id)
          } catch (e) { }
        }
      },
    })
  },

  cancelOrder() {
    wx.showModal({
      title: '取消订单',
      content: '确定要取消该订单吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.put(`/api/user/orders/${this.data.order.id}/cancel?reason=用户主动取消`)
            wx.showToast({ title: '已取消', icon: 'success' })
            this.loadOrder(this.data.order.id)
          } catch (e) { }
        }
      },
    })
  },
})
