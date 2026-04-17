import { useEffect, useRef, useState } from 'react'

export function useWebSocketLogs() {
  const [logs, setLogs] = useState([])
  const wsRef = useRef(null)
  const reconnectTimer = useRef(null)

  const connect = () => {
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/logs`)
    wsRef.current = ws

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data)
        if (data.type === 'ping') return
        setLogs((prev) => [data, ...prev].slice(0, 500)) // keep last 500
      } catch (_) {}
    }

    ws.onclose = () => {
      reconnectTimer.current = setTimeout(connect, 3000)
    }

    ws.onerror = () => ws.close()
  }

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      clearTimeout(reconnectTimer.current)
    }
  }, [])

  const clearLogs = () => setLogs([])

  return { logs, clearLogs }
}
