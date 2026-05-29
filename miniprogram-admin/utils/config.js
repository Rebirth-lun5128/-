/** 开发环境 API 地址（生产环境请改为 HTTPS 域名） */
const PORT = 8000
const HOST_SIMULATOR = '127.0.0.1'
// 真机预览/调试：改成你电脑的局域网 IP（cmd 执行 ipconfig 查看）
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

module.exports = { getApiBase, getWsBase, HOST_DEVICE, PORT }
