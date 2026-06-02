'use client'
import { useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { useSSE } from '@/hooks/useSSE'
import { useToast } from '@/contexts/ToastContext'
import { Sidebar } from '@/components/layout/Sidebar'
import { api } from '@/lib/api'
import { Autorizacion } from '@/lib/types'
import { estadoLabel } from '@/components/ui/Badge'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, token } = useAuth()
  const router = useRouter()
  const { showToast } = useToast()
  const [hitlCount, setHitlCount] = useState(0)
  const [urgentesCount, setUrgentesCount] = useState(0)

  const pathname = usePathname()

  useEffect(() => {
    if (!user) { router.replace('/'); return }
    
    // RBAC: Route Protection
    const r = user.rol
    if (r === 'recepcionista' && ['/dashboard', '/hitl', '/auditoria'].includes(pathname)) {
      router.replace('/autorizaciones'); return
    }
    if (r === 'supervisor' && pathname === '/auditoria') {
      router.replace('/dashboard'); return
    }
    if (r === 'auditor' && pathname !== '/auditoria') {
      router.replace('/auditoria'); return
    }

    refreshCounts()
    const interval = setInterval(refreshCounts, 30_000)
    return () => clearInterval(interval)
  }, [user, pathname, router])

  async function refreshCounts() {
    const [m, a] = await Promise.all([api.getMetricas(), api.getAutorizaciones()])
    if (m) setHitlCount(m.pendientes_hitl)
    if (a) setUrgentesCount((a as Autorizacion[]).filter(x => x.urgencia === 'urgente').length)
  }

  useSSE(token, (ev) => {
    if (ev.tipo === 'autorizacion_procesada') {
      showToast(ev.estado === 'autorizado' ? 'success' : 'warning', 'Nueva autorización', `${ev.paciente || 'Paciente'} · ${estadoLabel(String(ev.estado))}`)
      refreshCounts()
    } else if (ev.tipo === 'hitl_resuelto') {
      showToast('info', 'HITL resuelto', `Decisión: ${ev.decision}`)
      refreshCounts()
    }
  })

  if (!user) return null

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar hitlCount={hitlCount} urgentesCount={urgentesCount} />
      <main className="flex-1 flex flex-col overflow-hidden">
        {children}
      </main>
    </div>
  )
}
