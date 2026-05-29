/** 获取订单状态文本 */
export function getOrderStatusText(s) {
  const map = {
    pending_pay: '待支付', pending: '处理中', pending_accept: '等待接单',
    preparing: '备餐中', ready: '待取餐', delivering: '配送中',
    delivered: '已送达', completed: '已完成', partial: '部分完成', cancelled: '已取消',
  }
  return map[s] || s
}

/** 获取订单状态颜色 */
export function getOrderStatusColor(s) {
  const map = {
    pending_pay: '#FF9800', pending: '#FF6B35', pending_accept: '#FF6B35',
    preparing: '#2196F3', ready: '#4CAF50', delivering: '#2196F3',
    delivered: '#4CAF50', completed: '#999', partial: '#FF9800', cancelled: '#999',
  }
  return map[s] || '#999'
}

/** 是否需要支付 */
export function needPay(status) {
  return status === 'pending_pay'
}
