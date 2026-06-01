import { NextRequest } from 'next/server'

const API_BASE = process.env.API_BASE || 'http://localhost:8002'

export async function GET(request: NextRequest) {
  const token = request.nextUrl.searchParams.get('token') || ''
  const url = `${API_BASE}/api/v1/notificaciones/stream?token=${token}`

  const upstream = await fetch(url, {
    headers: { Accept: 'text/event-stream' },
  })

  return new Response(upstream.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
