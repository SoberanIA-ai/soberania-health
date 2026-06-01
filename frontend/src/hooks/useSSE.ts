'use client'
import { useEffect, useRef } from 'react'

interface SSEEvent {
  tipo: string
  [key: string]: unknown
}

const API_BASE = 'http://localhost:8002'

export function useSSE(token: string | null, onEvent: (ev: SSEEvent) => void) {
  const cbRef = useRef(onEvent)
  cbRef.current = onEvent

  useEffect(() => {
    if (!token) return
    const src = new EventSource(`${API_BASE}/api/v1/notificaciones/stream?token=${token}`)

    src.onmessage = (e) => {
      try {
        const ev = JSON.parse(e.data)
        if (ev.tipo !== 'conectado') cbRef.current(ev)
      } catch { /* ignore malformed */ }
    }

    return () => src.close()
  }, [token])
}
