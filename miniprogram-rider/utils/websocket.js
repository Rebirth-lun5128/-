const { getWsBase } = require('./config')

const RECONNECT_DELAY = 5000
const MAX_RETRIES = 3

let socketTask = null
let retryCount = 0
let listeners = {}
let isManualClose = false
let pingTimer = null

function connect() {
  const token = wx.getStorageSync('rider_token')
  if (!token || socketTask) return

  isManualClose = false
  socketTask = wx.connectSocket({
    url: getWsBase() + '/ws?token=' + encodeURIComponent(token),
    fail: () => { socketTask = null },
  })

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
    if (pingTimer) clearInterval(pingTimer)
    pingTimer = null
    socketTask = null
    if (!isManualClose && retryCount < MAX_RETRIES) {
      retryCount++
      setTimeout(connect, RECONNECT_DELAY * retryCount)
    }
  })

  socketTask.onError(() => {
    if (pingTimer) clearInterval(pingTimer)
    pingTimer = null
    socketTask = null
  })
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
  if (pingTimer) clearInterval(pingTimer)
  pingTimer = null
  if (socketTask) {
    socketTask.close()
    socketTask = null
  }
}

module.exports = { connect, on, off, close }
