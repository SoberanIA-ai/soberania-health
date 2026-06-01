'use client'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Autorizacion } from '@/lib/types'
import { ConfidenceBar } from '@/components/ui/ConfidenceBar'
import { DetailDrawer } from '@/components/autorizaciones/DetailDrawer'
import { Spinner } from '@/components/ui/Spinner'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/contexts/ToastContext'
import { iniciales, avatarColor, aseguraClass, capitalize, fmtDate } from '@/lib/utils'

export default function HitlPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [autorizaciones, setAutorizaciones] = useState<Autorizacion[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<Autorizacion | null>(null)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    const a = await api.getAutorizaciones()
    if (a) setAutorizaciones((a as Autorizacion[]).filter(x => x.estado === 'pendiente_hitl'))
    setLoading(false)
  }

  async function quickHITL(id: string, decision: string, e: React.MouseEvent) {
    e.stopPropagation()
    const revisor = user?.email || 'dashboard_user'
    const r = await api.aplicarHITL(id, decision, revisor, '')
    if (!r) return
    if (!r.ok) { const d = await r.json(); showToast('error', 'Error', d.detail || ''); return }
    showToast('success', 'HITL actualizado', decision === 'aprobar' ? 'Caso aprobado.' : 'Caso rechazado.')
    loadData()
  }

  return (
    <>
      <div className="bg-white px-6 py-4 border-b border-gray-200 shrink-0">
        <h1 className="text-lg font-bold text-gray-900">Cola de Revisión HITL</h1>
        <p className="text-sm text-gray-500">Casos que requieren supervisión humana</p>
      </div>

      <div className="flex-1 overflow-y-auto p-6 min-h-0">
        {loading && <div className="flex justify-center py-12"><Spinner size={24} /></div>}

        {!loading && (
          <div className="bg-white rounded-xl border border-gray-200">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    {['Paciente','Aseguradora','Procedimiento','Confidence','Fecha','Acciones'].map(h => (
                      <th key={h} className="px-3.5 py-2.5 text-left text-xs font-semibold text-gray-500 bg-gray-50 border-b border-gray-200">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {autorizaciones.length === 0 && (
                    <tr><td colSpan={6} className="py-10 text-center text-sm text-gray-400">✅ No hay casos pendientes de revisión.</td></tr>
                  )}
                  {autorizaciones.map(a => (
                    <tr key={a.id} onClick={() => setSelected(a)} className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer">
                      <td className="px-3.5 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0" style={{ background: avatarColor(a.paciente_nombre) }}>
                            {iniciales(a.paciente_nombre)}
                          </div>
                          <div className="text-sm font-semibold text-gray-900">{a.paciente_nombre || 'Paciente'}</div>
                        </div>
                      </td>
                      <td className="px-3.5 py-3">
                        <span className={`text-sm font-semibold ${aseguraClass(a.aseguradora)}`}>{capitalize(a.aseguradora || '–')}</span>
                      </td>
                      <td className="px-3.5 py-3 max-w-[220px]">
                        <span className="text-sm text-gray-700 truncate block">{a.procedimiento_descripcion || '–'}</span>
                      </td>
                      <td className="px-3.5 py-3">
                        <ConfidenceBar value={a.confidence_score} maxWidth={80} />
                      </td>
                      <td className="px-3.5 py-3 text-sm text-gray-500">{fmtDate(a.created_at)}</td>
                      <td className="px-3.5 py-3" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-1">
                          <button onClick={() => setSelected(a)} className="w-7 h-7 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-500 flex items-center justify-center text-sm">👁</button>
                          <button onClick={e => quickHITL(a.id, 'aprobar', e)} className="w-7 h-7 rounded-md bg-verde-bg hover:bg-green-200 text-verde-ok flex items-center justify-center text-sm" title="Aprobar">✓</button>
                          <button onClick={e => quickHITL(a.id, 'rechazar', e)} className="w-7 h-7 rounded-md bg-rojo-bg hover:bg-red-200 text-rojo flex items-center justify-center text-sm" title="Rechazar">✕</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      <DetailDrawer autorizacion={selected} onClose={() => setSelected(null)} onRefresh={loadData} />
    </>
  )
}
