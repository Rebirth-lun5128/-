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
    // 改动申请
    showModSheet: false,
    showModDialog: false,
    modType: '',
    modTypes: [
      { type: 'cancel', label: '退单申请', icon: '↩️', desc: '不想要了，申请取消订单' },
      { type: 'refund', label: '退款申请', icon: '💰', desc: '已支付，申请退款' },
      { type: 'address_change', label: '修改地址', icon: '📍', desc: '修改收货地址信息' },
      { type: 'other', label: '其他申请', icon: '💬', desc: '其他需要调整的地方' },
    ],
    modSubId: null,
    modReason: '',
    modAddressChanged: false,
    modContactName: '',
    modContactPhone: '',
    modAddressDetail: '',
    modifications: [],
    modPending: false,
    submittingMod: false,
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
      if (data.event === 'modification_reviewed' || data.event === 'modification_requested') {
        this.loadModifications()
      }
      this.loadOrder(this.orderId)
    })
  },

  async loadOrder(id) {
    try {
      const order = await api.get(`/api/user/orders/${id}`)
      const addr = order.address_snapshot
      const destLat = addr.lat || null
      const destLng = addr.lng || null

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
    this.loadModifications()
  },

  // ==================== 改动申请 ====================

  async loadModifications() {
    try {
      const mods = await api.get(`/api/user/orders/${this.orderId}/modifications`)
      const pendingMod = mods.find(m => m.status === 'pending_review')
      this.setData({
        modifications: mods || [],
        modPending: !!pendingMod,
      })
    } catch (e) { }
  },

  showModifySheet() {
    this.setData({ showModSheet: true })
  },

  closeModSheet() {
    this.setData({ showModSheet: false })
  },

  selectModType(e) {
    const type = e.currentTarget.dataset.type
    this.setData({ showModSheet: false, modType: type })

    if (type === 'address_change') {
      // 地址修改：初始化地址表单
      const addr = (this.data.order && this.data.order.address_snapshot) || {}
      this.setData({
        modSubId: null,
        modReason: '',
        modContactName: addr.contact_name || '',
        modContactPhone: addr.contact_phone || '',
        modAddressDetail: addr.detail || addr.address || '',
        modAddressChanged: false,
      })
    } else {
      this.setData({
        modSubId: null,
        modReason: '',
      })
    }
    // 延迟显示弹窗，防止 ActionSheet 关闭事件穿透
    setTimeout(() => { this.setData({ showModDialog: true }) }, 300)
  },

  closeModDialog() {
    this.setData({ showModDialog: false })
  },

  onModSubChange(e) {
    this.setData({ modSubId: parseInt(e.detail.value) })
  },

  onModReasonInput(e) {
    this.setData({ modReason: e.detail.value })
  },

  onModNameInput(e) { this.setData({ modContactName: e.detail.value, modAddressChanged: true }) },
  onModPhoneInput(e) { this.setData({ modContactPhone: e.detail.value, modAddressChanged: true }) },
  onModAddrInput(e) { this.setData({ modAddressDetail: e.detail.value, modAddressChanged: true }) },

  async submitMod() {
    const { modType, modReason } = this.data
    if (!modReason.trim()) {
      wx.showToast({ title: '请填写申请理由', icon: 'none' })
      return
    }

    this.setData({ submittingMod: true })
    try {
      if (modType === 'address_change') {
        // 总单级别改动
        await api.post(`/api/user/orders/${this.orderId}/request-modification`, {
          type: modType,
          reason: modReason.trim(),
          new_address: {
            contact_name: this.data.modContactName,
            contact_phone: this.data.modContactPhone,
            detail: this.data.modAddressDetail,
          },
        })
      } else {
        // 子单级别改动
        const subId = this.data.modSubId || (this.data.subOrders.length === 1 ? this.data.subOrders[0].id : null)
        if (!subId) {
          wx.showToast({ title: '请选择要修改的店铺', icon: 'none' })
          this.setData({ submittingMod: false })
          return
        }
        await api.post(`/api/user/orders/sub/${subId}/request-modification`, {
          type: modType,
          reason: modReason.trim(),
        })
      }
      wx.showToast({ title: '申请已提交，等待审核', icon: 'success' })
      this.setData({ showModDialog: false, submittingMod: false })
      this.loadModifications()
    } catch (e) {
      this.setData({ submittingMod: false })
    }
  },

  modTypeLabel(type) {
    const map = { cancel: '退单申请', refund: '退款申请', address_change: '修改地址', other: '其他申请' }
    return map[type] || type
  },

  modStatusLabel(s) {
    const map = { pending_review: '待审核', approved: '已通过', rejected: '已拒绝' }
    return map[s] || s
  },

  modStatusColor(s) {
    const map = { pending_review: '#FF9800', approved: '#4CAF50', rejected: '#999' }
    return map[s] || '#999'
  },

  // ==================== 评价 ====================

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
