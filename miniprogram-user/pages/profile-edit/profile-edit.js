const api = require('../../utils/api')
const app = getApp()

Page({
  data: {
    nickname: '',
    phone: '',
    avatar: '',
    originalPhone: '',
    originalNickname: '',
    originalAvatar: '',
    changed: false,
    saving: false,
  },

  onLoad() {
    this.loadUser()
  },

  loadUser() {
    const user = app.globalData.userInfo
    if (user) {
      this.setData({
        nickname: user.nickname || '',
        phone: user.phone || '',
        avatar: user.avatar || '',
        originalPhone: user.phone || '',
        originalNickname: user.nickname || '',
        originalAvatar: user.avatar || '',
      })
    }
  },

  chooseAvatar() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        const tempPath = res.tempFiles[0].tempFilePath
        // 实际项目中应上传到 CDN，这里直接存临时路径供演示
        this.setData({ avatar: tempPath })
        this.checkChanged()
      },
    })
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value })
    this.checkChanged()
  },

  onPhoneInput(e) {
    this.setData({ phone: e.detail.value })
    this.checkChanged()
  },

  checkChanged() {
    const changed =
      this.data.nickname !== this.data.originalNickname ||
      this.data.phone !== this.data.originalPhone ||
      this.data.avatar !== this.data.originalAvatar
    this.setData({ changed })
  },

  async onSave() {
    if (!this.data.changed || this.data.saving) return

    const phone = this.data.phone.trim()
    if (phone && !/^1\d{10}$/.test(phone)) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' })
      return
    }

    this.setData({ saving: true })
    try {
      const body = {}
      if (this.data.nickname !== this.data.originalNickname) {
        body.nickname = this.data.nickname.trim()
      }
      if (this.data.phone !== this.data.originalPhone) {
        body.phone = phone
      }
      if (this.data.avatar !== this.data.originalAvatar) {
        body.avatar = this.data.avatar
      }

      const res = await api.put('/api/common/auth/profile', body)
      // 更新 globalData
      app.globalData.userInfo = res
      wx.setStorageSync('userInfo', res)

      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 800)
    } catch (e) {} finally {
      this.setData({ saving: false })
    }
  },
})
