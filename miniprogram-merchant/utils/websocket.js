const { getWsBase, checkBackend } = require('./config')

const RECONNECT_DELAY = 8000
const MAX_RETRIES = 2

let socketTask = null
let retryCount = 0
let listeners = {}
let isManualClose = false
let pingTimer = null
let connecting = false

function connect() {
  const token = wx.getStorageSync('merchant_token')
  if (!token || socketTask || connecting) return

  isManualClose = false
  connecting = true
  checkBackend().then((ok) => {
    connecting = false
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
      ;(listeners[data.event] || []).forEach((fn) => fn(data))
      ;(listeners['*'] || []).forEach((fn) => fn(data))
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
  if (!listeners[event].includes(callback)) {
    listeners[event].push(callback)
  }
}

function off(event, callback) {
  if (!listeners[event]) return
  listeners[event] = listeners[event].filter((fn) => fn !== callback)
}

function close() {
  isManualClose = true
  retryCount = MAX_RETRIES
  connecting = false
  clearPingTimer()
  if (socketTask) {
    socketTask.close()
    socketTask = null
  }
}

module.exports = { connect, on, off, close }
