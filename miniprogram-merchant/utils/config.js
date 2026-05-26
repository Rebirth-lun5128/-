const PORT = 8000
const HOST_SIMULATOR = '127.0.0.1'
const HOST_DEVICE = '192.168.18.6'

function getHost() {
  try {
    if (wx.getSystemInfoSync().platform === 'devtools') return HOST_SIMULATOR
  } catch (_) {}
  return HOST_DEVICE
}

function getApiBase() {
  return `http://${getHost()}:${PORT}`
}

function getWsBase() {
  return `ws://${getHost()}:${PORT}`
}

function checkBackend() {
  return new Promise((resolve) => {
    wx.request({
      url: getApiBase() + '/health',
      timeout: 5000,
      success: (res) => resolve(res.statusCode === 200),
      fail: () => resolve(false),
    })
  })
}

module.exports = { getApiBase, getWsBase, checkBackend, HOST_DEVICE, PORT }
