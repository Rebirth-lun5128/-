function getStatusText(status) {
  const map = {
    pending_pay: '待支付', pending_accept: '待接单', preparing: '备餐中',
    ready: '待取餐', delivering: '配送中', completed: '已完成', cancelled: '已取消',
  }
  return map[status] || status
}

function getVerifyText(s) {
  const map = { unverified: '待核验', verified: '已通过', rejected: '已拒绝' }
  return map[s] || s
}

function getAuditText(s) {
  const map = { pending: '待审核', approved: '已通过', rejected: '已拒绝' }
  return map[s] || s
}

function getStoreTypeText(s) {
  const map = { stall: '夜市摊位', home_kitchen: '家庭厨房', self_operated: '平台自营' }
  return map[s] || s
}

module.exports = { getStatusText, getVerifyText, getAuditText, getStoreTypeText }
