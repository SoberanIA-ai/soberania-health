'use client'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Autorizacion, Metricas } from '@/lib/types'
import { DonutChart, AseguradoraChart } from '@/components/dashboard/Charts'
import { DetailDrawer } from '@/components/autorizaciones/DetailDrawer'
import { Spinner } from '@/components/ui/Spinner'
import { pct, iniciales, avatarColor, capitalize } from '@/lib/utils'

function KpiCard({ icon, num, label, sub, numColor, bgColor }: { icon: string; num: string | number; label: string; sub?: string; numColor?: string; bgColor?: string }) {
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-200">
      <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg mb-2" style={{ background: bgColor || '#eff6ff' }}>{icon}</div>
      <div className="text-2xl font-bold leading-none" style={{ color: numColor || '#111827' }}>{num}</div>
      <div className="text-xs text-gray-500 font-medium mt-1">{label}</div>
      {sub && <div className="text-xs font-semibold mt-0.5" style={{ color: numColor || '#6b7280' }}>{sub}</div>}
    </div>
  )
}

export default function DashboardPage() {
  const [metricas, setMetricas] = useState<Metricas | null>(null)
  const [autorizaciones, setAutorizaciones] = useState<Autorizacion[]>([])
  const [selected, setSelected] = useState<Autorizacion | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    const [m, a] = await Promise.all([api.getMetricas(), api.getAutorizaciones()])
    if (m) setMetricas(m)
    if (a) setAutorizaciones(a)
    setLoading(false)
  }

  const urgentes = autorizaciones.filter(a => a.urgencia === 'urgente')
  const total = metricas?.total || 0

  return (
    <>
      {/* Header */}
      <div className="bg-white px-6 py-4 border-b border-gray-200 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-lg font-bold text-gray-900">Dashboard de Autorizaciones</h1>
          <p className="text-sm text-gray-500">Vista general del estado de autorizaciones con aseguradoras</p>
        </div>
        <span className="text-sm text-gray-400">
          {new Date().toLocaleDateString('es-ES', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6 min-h-0">
        {loading && <div className="flex justify-center py-12"><Spinner size={24} /></div>}

        {!loading && (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-5 gap-3.5 mb-5">
              <KpiCard icon="📁" num={total.toLocaleString('es-ES')} label="Total autorizaciones" sub="Todas las aseguradoras" bgColor="#eff6ff" />
              <KpiCard icon="⏰" num={metricas?.pendientes_hitl ?? 0} label="Pendiente revisión" sub={total > 0 ? pct(metricas?.pendientes_hitl ?? 0, total) + '% del total' : ''} numColor="#d97706" bgColor="#fef3c7" />
              <KpiCard icon="✅" num={metricas?.autorizadas ?? 0} label="Autorizadas" sub={total > 0 ? pct(metricas?.autorizadas ?? 0, total) + '% del total' : ''} numColor="#16a34a" bgColor="#dcfce7" />
              <KpiCard icon="❌" num={metricas?.denegadas ?? 0} label="Rechazadas" sub={total > 0 ? pct(metricas?.denegadas ?? 0, total) + '% del total' : ''} numColor="#dc2626" bgColor="#fee2e2" />
              <KpiCard icon="🚨" num={urgentes.length} label="Urgentes" sub={total > 0 ? pct(urgentes.length, total) + '% del total' : ''} numColor="#ef4444" bgColor="#fee2e2" />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-3 gap-3.5 mb-5" style={{ gridTemplateColumns: '1fr 1fr 280px' }}>
              <DonutChart autorizaciones={autorizaciones} />
              <AseguradoraChart autorizaciones={autorizaciones} />

              {/* Urgentes panel */}
              <div className="bg-white rounded-xl p-5 border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Urgentes</h3>
                {urgentes.length === 0 && <p className="text-sm text-gray-400">No hay casos urgentes.</p>}
                {urgentes.slice(0, 4).map(a => (
                  <div key={a.id} className="flex items-center gap-2.5 py-2 border-b border-gray-50 last:border-none cursor-pointer hover:bg-gray-50 rounded" onClick={() => setSelected(a)}>
                    <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-rojo bg-rojo-bg shrink-0">{iniciales(a.paciente_nombre)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold text-gray-900 truncate">{a.paciente_nombre || 'Paciente'}</div>
                      <div className="text-xs text-gray-500 truncate">{capitalize(a.aseguradora || '')} · {a.procedimiento_descripcion || ''}</div>
                    </div>
                    <span className="text-[10px] font-bold bg-rojo-urg text-white px-1.5 py-0.5 rounded">URGENTE</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>

      <DetailDrawer autorizacion={selected} onClose={() => setSelected(null)} onRefresh={loadData} />
    </>
  )
}
