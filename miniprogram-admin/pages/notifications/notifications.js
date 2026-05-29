const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    isSuperAdmin: true,
    // 发送表单
    title: '',
    content: '',
    targetRole: 'user',
    targetRoleLabel: '用户',
    sending: false,
    // 记录列表
    items: [],
    total: 0,
    page: 1,
    loading: false,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.setData({ isSuperAdmin: app.isSuperAdmin() })
    this.loadHistory()
  },

  // --- 发送 ---
  onTitleInput(e) { this.setData({ title: e.detail.value }) },
  onContentInput(e) { this.setData({ content: e.detail.value }) },

  onRoleChange(e) {
    const roles = ['user', 'merchant', 'rider', 'all']
    const labels = ['用户', '商家', '骑手', '全部']
    const idx = e.detail.value
    this.setData({ targetRole: roles[idx], targetRoleLabel: labels[idx] })
  },

  async sendNotification() {
    const { title, content, targetRole, sending } = this.data
    if (sending || !title.trim()) return
    this.setData({ sending: true })
    try {
      const res = await api.post('/api/admin/notifications/send', {
        title: title.trim(),
        content: content.trim(),
        target_role: targetRole,
      })
      wx.showToast({ title: res.message || '已发送', icon: 'success' })
      this.setData({ title: '', content: '', page: 1 })
      this.loadHistory()
    } catch (e) {} finally {
      this.setData({ sending: false })
    }
  },

  // --- 记录 ---
  async loadHistory() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/api/admin/notifications', { page: this.data.page, page_size: 20 })
      const labelMap = { user: '用户', merchant: '商家', rider: '骑手', all: '全部' }
      const items = (res.items || []).map(item => ({
        ...item,
        roleLabel: labelMap[item.target_role] || item.target_role,
      }))
      this.setData({ items, total: res.total || 0 })
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },

  roleLabel(r) {
    const map = { user: '用户', merchant: '商家', rider: '骑手', all: '全部' }
    return map[r] || r
  },
})
