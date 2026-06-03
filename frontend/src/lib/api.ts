const API_BASE = 'http://localhost:8002'

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('soberania_token')
}

async function apiFetch(url: string, opts: RequestInit = {}): Promise<Response | null> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(opts.headers as Record<string, string> || {}),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  try {
    const r = await fetch(`${API_BASE}${url}`, { ...opts, headers })
    if (r.status === 401) {
      window.dispatchEvent(new Event('soberania:logout'))
      return null
    }
    return r
  } catch {
    return null
  }
}

export const api = {
  async login(email: string, password: string) {
    try {
      return fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
    } catch {
      return null
    }
  },

  async getMetricas() {
    const r = await apiFetch('/api/v1/autorizaciones/metricas')
    if (!r?.ok) return null
    return r.json()
  },

  async getAutorizaciones(limit = 200) {
    const r = await apiFetch(`/api/v1/autorizaciones/?limit=${limit}`)
    if (!r?.ok) return null
    return r.json()
  },

  async getMetricasAIAct() {
    const r = await apiFetch('/api/v1/autorizaciones/metricas-aiact')
    if (!r?.ok) return null
    return r.json()
  },

  async getAudit(id: string) {
    const r = await apiFetch(`/api/v1/audit/${id}`)
    if (!r?.ok) return null
    return r.json()
  },

  async getAIActReport(id: string) {
    const r = await apiFetch(`/api/v1/audit/${id}/aiact-report`)
    if (!r?.ok) return null
    return r.json()
  },

  async procesar(ordenH17: string) {
    return apiFetch('/api/v1/autorizaciones/procesar', {
      method: 'POST',
      body: JSON.stringify({ orden_h17: ordenH17, modo: 'mock' }),
    })
  },

  async aplicarHITL(id: string, decision: string, revisor: string, notas: string) {
    return apiFetch(`/api/v1/autorizaciones/${id}/hitl`, {
      method: 'POST',
      body: JSON.stringify({ decision, revisor, notas }),
    })
  },

  async reenviar(id: string, notasAdicionales: string, archivosAdjuntos: string[]) {
    return apiFetch(`/api/v1/autorizaciones/${id}/reenviar`, {
      method: 'POST',
      body: JSON.stringify({ notas_adicionales: notasAdicionales, archivos_adjuntos: archivosAdjuntos }),
    })
  },
}
