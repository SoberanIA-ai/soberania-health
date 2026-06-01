import { NextRequest, NextResponse } from 'next/server'

const API_BASE = process.env.API_BASE || 'http://localhost:8002'

function forwardHeaders(request: NextRequest): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  const auth = request.headers.get('Authorization')
  if (auth) h['Authorization'] = auth
  return h
}

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join('/')
  const search = request.nextUrl.search
  const url = `${API_BASE}/api/v1/${path}${search}`
  const res = await fetch(url, { headers: forwardHeaders(request) })
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const path = params.path.join('/')
  const url = `${API_BASE}/api/v1/${path}`
  const body = await request.text()
  const res = await fetch(url, { method: 'POST', headers: forwardHeaders(request), body })
  const data = await res.json()
  return NextResponse.json(data, { status: res.status })
}
