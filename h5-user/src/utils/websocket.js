const MAX_RETRIES = 3
const PING_INTERVAL = 30000

let socket = null
let listeners = {}
let retryCount = 0
let pingTimer = null
let isManualClose = false

export function connectWS() {
  const token = localStorage.getItem('token')
  if (!token) return

  if (socket && socket.readyState === WebSocket.OPEN) return

  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${protocol}://${location.host}/ws?token=${token}`

  socket = new WebSocket(url)

  socket.onopen = () => {
    console.log('[WS] 已连接')
    retryCount = 0
    startPing()
  }

  socket.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      if (data.type === 'pong') return
      const type = data.type || data.event
      if (type) {
        if (listeners[type]) {
          listeners[type].forEach((fn) => fn(data))
        }
        if (listeners['*']) {
          listeners['*'].forEach((fn) => fn(data))
        }
      }
    } catch {}
  }

  socket.onclose = () => {
    stopPing()
    if (isManualClose) return
    if (retryCount < MAX_RETRIES) {
      const delay = Math.min(1000 * Math.pow(2, retryCount), 10000)
      retryCount++
      console.log(`[WS] 断开，${delay / 1000}s后重连 (${retryCount}/${MAX_RETRIES})`)
      setTimeout(connectWS, delay)
    } else {
      console.log('[WS] 已达最大重试次数，停止重连')
    }
  }

  socket.onerror = () => {
    stopPing()
    if (socket) socket.close()
  }
}

function startPing() {
  stopPing()
  pingTimer = setInterval(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      try { socket.send(JSON.stringify({ type: 'ping' })) } catch {}
    }
  }, PING_INTERVAL)
}

function stopPing() {
  if (pingTimer) {
    clearInterval(pingTimer)
    pingTimer = null
  }
}

export function onWSEvent(type, fn) {
  if (!listeners[type]) listeners[type] = []
  listeners[type].push(fn)
}

export function offWSEvent(type, fn) {
  if (listeners[type]) {
    listeners[type] = listeners[type].filter((f) => f !== fn)
  }
}

export function closeWS() {
  isManualClose = true
  stopPing()
  if (socket) {
    socket.close()
    socket = null
  }
  listeners = {}
  retryCount = 0
}
