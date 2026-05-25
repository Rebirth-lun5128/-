/** 格式化价格为显示文本 */
function formatPrice(price) {
  return (price || 0).toFixed(2)
}

/** 获取订单状态文本 */
function getOrderStatusText(status) {
  const map = {
    pending_pay: '待支付',
    pending_accept: '等待商家接单',
    preparing: '商家备餐中',
    ready: '等待骑手取餐',
    delivering: '配送中',
    delivered: '已送达',
    completed: '已完成',
    cancelled: '已取消',
  }
  return map[status] || status
}

/** 订单是否需要支付 */
function needPay(status) {
  return status === 'pending_pay'
}

/** 获取订单状态颜色 */
function getOrderStatusColor(status) {
  const map = {
    pending_pay: '#FF9800',
    pending_accept: '#FF6B35',
    preparing: '#2196F3',
    ready: '#4CAF50',
    delivering: '#2196F3',
    delivered: '#4CAF50',
    completed: '#999',
    cancelled: '#999',
  }
  return map[status] || '#999'
}

module.exports = {
  formatPrice,
  getOrderStatusText,
  getOrderStatusColor,
}
