const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    isSuperAdmin: true,
    items: [],
    loading: false,
    // 创建表单
    showCreate: false,
    phone: '',
    password: '',
    nickname: '',
    role: 'district_admin',
    roleLabel: '分区管理员',
    districtId: null,
    districtName: '',
    districts: [],
    submitting: false,
  },

  onShow() {
    if (!app.checkLogin()) return
    this.setData({ isSuperAdmin: app.isSuperAdmin() })
    this.loadData()
    this.loadDistricts()
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/api/admin/admins')
      this.setData({ items: Array.isArray(res) ? res : [] })
    } catch (e) {} finally {
      this.setData({ loading: false })
    }
  },

  async loadDistricts() {
    try {
      const res = await api.get('/api/admin/districts')
      const list = res.districts || res || []
      this.setData({ districts: list })
    } catch (e) {}
  },

  // ---- 创建 ----
  openCreate() {
    this.setData({ showCreate: true, phone: '', password: '', nickname: '', role: 'district_admin', roleLabel: '分区管理员', districtId: null, districtName: '' })
  },
  closeCreate() { this.setData({ showCreate: false }) },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onPwdInput(e) { this.setData({ password: e.detail.value }) },
  onNameInput(e) { this.setData({ nickname: e.detail.value }) },

  onRoleChange(e) {
    const roles = ['district_admin', 'super_admin']
    const labels = ['分区管理员', '超级管理员']
    this.setData({ role: roles[e.detail.value], roleLabel: labels[e.detail.value] })
  },

  onDistrictChange(e) {
    const idx = e.detail.value
    const d = this.data.districts[idx]
    this.setData({ districtId: d ? d.id : null, districtName: d ? d.name : '' })
  },

  async submitCreate() {
    const { phone, password, nickname, role, districtId, submitting } = this.data
    if (submitting || !phone || !password) return
    this.setData({ submitting: true })
    try {
      await api.post('/api/admin/admins', {
        phone, password, nickname: nickname || '管理员',
        role, district_id: role === 'district_admin' ? districtId : null,
      })
      wx.showToast({ title: '已创建', icon: 'success' })
      this.setData({ showCreate: false })
      this.loadData()
    } catch (e) {} finally {
      this.setData({ submitting: false })
    }
  },

  // ---- 启停 ----
  async toggleStatus(e) {
    const { id, status } = e.currentTarget.dataset
    try {
      await api.put(`/api/admin/admins/${id}/toggle-status`)
      wx.showToast({ title: status == 1 ? '已禁用' : '已启用', icon: 'success' })
      this.loadData()
    } catch (e) {}
  },

  // ---- 删除 ----
  async deleteAdmin(e) {
    const id = e.currentTarget.dataset.id
    wx.showModal({
      title: '确认删除',
      content: '确定删除该管理员吗？此操作不可撤销。',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await api.del(`/api/admin/admins/${id}`)
          wx.showToast({ title: '已删除', icon: 'success' })
          this.loadData()
        } catch (e) {}
      },
    })
  },
})
