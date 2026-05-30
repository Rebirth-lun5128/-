const { getApiBase } = require('./config')

function request(method, path, data) {
  return new Promise((resolve, reject) => {
    const token = wx.getStorageSync('admin_token')
    wx.request({
      url: getApiBase() + path,
      method,
      timeout: 15000,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      data,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          // token 过期或无效，清除登录状态并跳转登录页
          wx.removeStorageSync('admin_token')
          wx.removeStorageSync('admin_role')
          wx.removeStorageSync('admin_district_id')
          const app = getApp()
          if (app) {
            app.globalData.token = null
            app.globalData.role = null
            app.globalData.districtId = null
          }
          wx.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
          setTimeout(() => {
            wx.redirectTo({ url: '/pages/login/login' })
          }, 800)
          reject(new Error('未授权'))
        } else {
          const detail = res.data?.detail || '请求失败'
          wx.showToast({ title: detail, icon: 'none' })
          reject(new Error(detail))
        }
      },
      fail(err) {
        const msg = (err.errMsg || '').includes('timeout')
          ? '连接超时，请确认后端已启动'
          : '网络错误，请检查 API 地址'
        wx.showToast({ title: msg, icon: 'none', duration: 3000 })
        reject(err)
      },
    })
  })
}

module.exports = {
  get: (path, params) => {
    let url = path
    if (params) {
      const qs = Object.entries(params)
        .filter(([_, v]) => v !== '' && v !== null && v !== undefined)
        .map(([k, v]) => `${k}=${encodeURIComponent(v)}`)
        .join('&')
      if (qs) url += '?' + qs
    }
    return request('GET', url)
  },
  post: (path, data) => request('POST', path, data),
  put: (path, data) => request('PUT', path, data),
  delete: (path) => request('DELETE', path),
}
