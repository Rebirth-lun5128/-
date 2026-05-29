let socket = null
let listeners = {}

export function connectWS() {
  const token = localStorage.getItem('token')
  if (!token) return

  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const url = `${protocol}://${location.host}/ws?token=${token}`

  socket = new WebSocket(url)

  socket.onopen = () => console.log('[WS] 已连接')
  socket.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data)
      const type = data.type || data.event
      if (type && listeners[type]) {
        listeners[type].forEach((fn) => fn(data))
      }
    } catch {}
  }
  socket.onclose = () => {
    console.log('[WS] 断开，5秒后重连')
    setTimeout(connectWS, 5000)
  }
  socket.onerror = () => socket?.close()
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
  if (socket) {
    socket.close()
    socket = null
  }
  listeners = {}
}
