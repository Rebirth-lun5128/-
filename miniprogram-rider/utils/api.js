const BASE_URL = 'http://localhost:8000'

function request(url, options = {}) {
  const token = wx.getStorageSync('rider_token')
  const header = { 'Content-Type': 'application/json', ...(options.header || {}) }
  if (token) header['Authorization'] = `Bearer ${token}`

  return new Promise((resolve, reject) => {
    wx.request({
      url: BASE_URL + url,
      method: options.method || 'GET',
      data: options.data || {},
      header,
      success(res) {
        if (res.statusCode === 200) resolve(res.data)
        else if (res.statusCode === 401) {
          wx.removeStorageSync('rider_token')
          wx.navigateTo({ url: '/pages/login/login' })
          reject(res.data)
        } else {
          wx.showToast({ title: res.data.detail || '请求失败', icon: 'none' })
          reject(res.data)
        }
      },
      fail(err) {
        wx.showToast({ title: '网络错误', icon: 'none' })
        reject(err)
      },
    })
  })
}

module.exports = {
  get: (url, data) => request(url, { method: 'GET', data }),
  post: (url, data) => request(url, { method: 'POST', data }),
  put: (url, data) => request(url, { method: 'PUT', data }),
}
