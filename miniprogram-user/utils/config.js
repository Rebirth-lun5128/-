/** 开发环境 API 地址 */
const PORT = 8000
// Windows 微信开发者工具下 localhost 可能走 IPv6 导致超时，请用 127.0.0.1
const HOST_SIMULATOR = '127.0.0.1'
// 真机预览：改成电脑局域网 IP（cmd 执行 ipconfig）
const HOST_DEVICE = '192.168.18.6'

function getHost() {
  try {
    const { platform } = wx.getSystemInfoSync()
    if (platform === 'devtools') return HOST_SIMULATOR
  } catch (_) {}
  return HOST_DEVICE
}

function getApiBase() {
  return `http://${getHost()}:${PORT}`
}

function getWsBase() {
  return `ws://${getHost()}:${PORT}`
}

/** 检测后端是否已启动 */
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
