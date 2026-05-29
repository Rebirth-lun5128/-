App({
  globalData: {
    userInfo: null,
    token: '',
    role: '',
    districtId: null,
  },

  onLaunch() {
    const token = wx.getStorageSync('admin_token')
    if (token) {
      this.globalData.token = token
      this.globalData.role = wx.getStorageSync('admin_role') || ''
      this.globalData.districtId = wx.getStorageSync('admin_district_id') || null
    }
  },

  checkLogin() {
    if (!this.globalData.token) {
      wx.redirectTo({ url: '/pages/login/login' })
      return false
    }
    return true
  },

  isSuperAdmin() {
    return this.globalData.role === 'super_admin'
  },

  logout() {
    this.globalData.token = ''
    this.globalData.role = ''
    this.globalData.districtId = null
    wx.removeStorageSync('admin_token')
    wx.removeStorageSync('admin_role')
    wx.removeStorageSync('admin_district_id')
    wx.redirectTo({ url: '/pages/login/login' })
  },
})
