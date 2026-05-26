const { getApiBase } = require('./config')

function request(url, options = {}) {
  const token = wx.getStorageSync('rider_token')
  const header = { 'Content-Type': 'application/json', ...(options.header || {}) }
  if (token) header['Authorization'] = `Bearer ${token}`

  return new Promise((resolve, reject) => {
    wx.request({
      url: getApiBase() + url,
      method: options.method || 'GET',
      data: options.data || {},
      header,
      timeout: 15000,
      success(res) {
        if (res.statusCode === 200) resolve(res.data)
        else if (res.statusCode === 401) {
          wx.removeStorageSync('rider_token')
          wx.navigateTo({ url: '/pages/login/login' })
          reject(res.data)
        } else {
          if (!options.silent) {
            wx.showToast({ title: res.data.detail || '请求失败', icon: 'none' })
          }
          reject(res.data)
        }
      },
      fail(err) {
        if (!options.silent) {
          const msg = (err.errMsg || '').includes('timeout')
            ? '连接超时，请确认后端已启动'
            : '网络错误'
          wx.showToast({ title: msg, icon: 'none' })
        }
        reject(err)
      },
    })
  })
}

module.exports = {
  get: (url, data, opts) => request(url, { method: 'GET', data, ...opts }),
  post: (url, data, opts) => request(url, { method: 'POST', data, ...opts }),
  put: (url, data, opts) => request(url, { method: 'PUT', data, ...opts }),
}
