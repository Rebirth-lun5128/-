function getOrderStatusText(status) {
  const map = {
    pending_pay: '待支付',
    pending_accept: '新订单',
    preparing: '备餐中',
    ready: '待取餐',
    delivering: '配送中',
    delivered: '已送达',
    completed: '已完成',
    cancelled: '已取消',
  }
  return map[status] || status
}

function getOrderStatusColor(status) {
  const map = {
    pending_pay: '#FF9800',
    pending_accept: '#FF6B35',
    preparing: '#2196F3',
    ready: '#4CAF50',
    delivering: '#2196F3',
    completed: '#999',
    cancelled: '#999',
  }
  return map[status] || '#999'
}

module.exports = {
  getOrderStatusText,
  getOrderStatusColor,
}
