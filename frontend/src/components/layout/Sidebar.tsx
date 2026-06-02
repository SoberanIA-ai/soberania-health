'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { iniciales } from '@/lib/utils'

interface SidebarProps {
  hitlCount: number
  urgentesCount: number
}

const NAV = [
  { href: '/dashboard',       icon: '📊', label: 'Resumen', roles: ['admin', 'supervisor'] },
  { href: '/autorizaciones',  icon: '📋', label: 'Autorizaciones', roles: ['admin', 'recepcionista', 'supervisor'] },
  { href: '/hitl',            icon: '⏳', label: 'Cola HITL',    badge: 'hitl', roles: ['supervisor', 'admin'] },
  { href: '/urgentes',        icon: '🚨', label: 'Urgentes',     badge: 'urgentes', roles: ['recepcionista', 'supervisor', 'admin'] },
  { href: '/auditoria',       icon: '🛡️', label: 'Auditoría AI Act', roles: ['auditor', 'admin'] },
]

export function Sidebar({ hitlCount, urgentesCount }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { user, logout } = useAuth()

  function handleLogout() {
    logout()
    router.push('/')
  }

  return (
    <aside className="w-60 min-w-[240px] bg-azul-marino flex flex-col h-full overflow-y-auto">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <span className="text-2xl">🏥</span>
          <div>
            <div className="text-sm font-bold text-white">HM Hospitales</div>
            <div className="text-xs text-white/50">SoberanIA Health</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-2">
        {NAV.map(item => {
          if (!item.roles || !item.roles.includes(user?.rol || '')) return null
          const active = pathname === item.href
          const count = item.badge === 'hitl' ? hitlCount : item.badge === 'urgentes' ? urgentesCount : 0
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm font-medium transition-all mb-0.5 ${
                active ? 'bg-azul-acento text-white' : 'text-white/70 hover:bg-white/10 hover:text-white'
              }`}
            >
              <span className="w-5 text-center text-[15px]">{item.icon}</span>
              <span className="flex-1">{item.label}</span>
              {count > 0 && (
                <span className={`text-xs font-bold px-1.5 py-0.5 rounded-full text-white ${item.badge === 'urgentes' ? 'bg-naranja' : 'bg-rojo-urg'}`}>
                  {count}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* User */}
      <div className="p-3 border-t border-white/10">
        <div className="flex items-center gap-2.5 px-2 py-2">
          <div
            className="w-8 h-8 rounded-full bg-azul-acento flex items-center justify-center text-xs font-bold text-white shrink-0"
          >
            {iniciales(user?.nombre)}
          </div>
          <div className="min-w-0">
            <div className="text-sm font-semibold text-white truncate">{user?.nombre}</div>
            <div className="text-xs text-white/50 capitalize">{user?.rol}</div>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full mt-2 py-2 text-xs text-white/60 hover:text-white bg-white/5 hover:bg-white/10 rounded-lg transition-all"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
