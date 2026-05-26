/**
 * WebSocket 连接管理 — 用户端
 */
const { getWsBase, checkBackend } = require('./config')

const RECONNECT_DELAY = 5000
const MAX_RETRIES = 3

let socketTask = null
let retryCount = 0
let listeners = {}
let isManualClose = false
let pingTimer = null

function connect() {
  const token = wx.getStorageSync('token')
  if (!token || socketTask) return

  isManualClose = false
  checkBackend().then((ok) => {
    if (!ok || isManualClose) return
    socketTask = wx.connectSocket({
      url: getWsBase() + '/ws?token=' + encodeURIComponent(token),
      fail: () => {
        socketTask = null
      },
    })
    bindSocketEvents()
  })
}

function bindSocketEvents() {
  if (!socketTask) return

  socketTask.onOpen(() => {
    retryCount = 0
    if (pingTimer) clearInterval(pingTimer)
    pingTimer = setInterval(() => {
      if (socketTask) socketTask.send({ data: 'ping' })
    }, 30000)
  })

  socketTask.onMessage((res) => {
    try {
      const data = JSON.parse(res.data)
      if (data.event === 'pong') return
      const cbs = listeners[data.event] || []
      cbs.forEach((fn) => fn(data))
      const allCbs = listeners['*'] || []
      allCbs.forEach((fn) => fn(data))
    } catch (e) {}
  })

  socketTask.onClose(() => {
    clearPingTimer()
    socketTask = null
    if (!isManualClose && retryCount < MAX_RETRIES) {
      retryCount++
      setTimeout(connect, RECONNECT_DELAY * retryCount)
    }
  })

  socketTask.onError(() => {
    clearPingTimer()
    socketTask = null
  })
}

function clearPingTimer() {
  if (pingTimer) {
    clearInterval(pingTimer)
    pingTimer = null
  }
}

function on(event, callback) {
  if (!listeners[event]) listeners[event] = []
  listeners[event].push(callback)
}

function off(event, callback) {
  if (!listeners[event]) return
  listeners[event] = listeners[event].filter((fn) => fn !== callback)
}

function close() {
  isManualClose = true
  retryCount = MAX_RETRIES
  clearPingTimer()
  if (socketTask) {
    socketTask.close()
    socketTask = null
  }
}

module.exports = { connect, on, off, close }
