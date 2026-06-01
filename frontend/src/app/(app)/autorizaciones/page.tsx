'use client'
import { useEffect, useState, useMemo } from 'react'
import { api } from '@/lib/api'
import { Autorizacion } from '@/lib/types'
import { BadgeEstado } from '@/components/ui/Badge'
import { ConfidenceBar } from '@/components/ui/ConfidenceBar'
import { DetailDrawer } from '@/components/autorizaciones/DetailDrawer'
import { NewAuthModal } from '@/components/autorizaciones/NewAuthModal'
import { Spinner } from '@/components/ui/Spinner'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/contexts/ToastContext'
import { api as apiLib } from '@/lib/api'
import { iniciales, avatarColor, aseguraClass, capitalize, fmtDate } from '@/lib/utils'

const TABS = [
  { label: 'Todas', filter: 'all' },
  { label: 'En proceso', filter: 'en_proceso,recibido' },
  { label: 'Pendiente HITL', filter: 'pendiente_hitl' },
  { label: 'Urgentes', filter: 'urgente' },
  { label: 'Autorizadas', filter: 'autorizado,aprobado_hitl' },
  { label: 'Rechazadas', filter: 'denegado,rechazado_hitl' },
]

const PAGE_SIZE = 20

export default function AutorizacionesPage() {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [autorizaciones, setAutorizaciones] = useState<Autorizacion[]>([])
  const [loading, setLoading] = useState(true)
  const [activeFilter, setActiveFilter] = useState('all')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const [selected, setSelected] = useState<Autorizacion | null>(null)
  const [modalOpen, setModalOpen] = useState(false)

  useEffect(() => { loadData() }, [])

  async function loadData() {
    const a = await api.getAutorizaciones()
    if (a) setAutorizaciones(a)
    setLoading(false)
  }

  const filtered = useMemo(() => {
    let rows = [...autorizaciones]
    if (activeFilter !== 'all') {
      if (activeFilter === 'urgente') rows = rows.filter(a => a.urgencia === 'urgente')
      else { const f = activeFilter.split(','); rows = rows.filter(a => f.includes(a.estado)) }
    }
    if (search) {
      const q = search.toLowerCase()
      rows = rows.filter(a =>
        (a.paciente_nombre || '').toLowerCase().includes(q) ||
        (a.aseguradora || '').toLowerCase().includes(q) ||
        (a.numero_autorizacion || '').toLowerCase().includes(q) ||
        (a.procedimiento_descripcion || '').toLowerCase().includes(q)
      )
    }
    return rows
  }, [autorizaciones, activeFilter, search])

  const pages = Math.ceil(filtered.length / PAGE_SIZE)
  const slice = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  function changeFilter(f: string) { setActiveFilter(f); setPage(0) }

  async function quickHITL(id: string, decision: string, e: React.MouseEvent) {
    e.stopPropagation()
    const revisor = user?.email || 'dashboard_user'
    const r = await apiLib.aplicarHITL(id, decision, revisor, '')
    if (!r) return
    if (!r.ok) { const d = await r.json(); showToast('error', 'Error', d.detail || ''); return }
    showToast('success', 'HITL actualizado', decision === 'aprobar' ? 'Caso aprobado.' : 'Caso rechazado.')
    loadData()
  }

  return (
    <>
      <div className="bg-white px-6 py-4 border-b border-gray-200 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-lg font-bold text-gray-900">Autorizaciones</h1>
          <p className="text-sm text-gray-500">Gestión de todas las autorizaciones médicas</p>
        </div>
        <button onClick={() => setModalOpen(true)} className="flex items-center gap-1.5 px-3.5 py-2 bg-azul-acento text-white text-sm font-semibold rounded-lg hover:bg-blue-700">
          + Nueva autorización
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 min-h-0">
        {loading && <div className="flex justify-center py-12"><Spinner size={24} /></div>}

        {!loading && (
          <div className="bg-white rounded-xl border border-gray-200">
            {/* Toolbar */}
            <div className="px-4 py-3 border-b border-gray-100 flex items-center gap-3 flex-wrap">
              <div className="flex gap-1 flex-wrap flex-1">
                {TABS.map(t => (
                  <button key={t.filter} onClick={() => changeFilter(t.filter)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${activeFilter === t.filter ? 'bg-azul-acento text-white border-azul-acento' : 'bg-white text-gray-500 border-gray-200 hover:bg-gray-50'}`}>
                    {t.label}
                  </button>
                ))}
              </div>
              <div className="relative">
                <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
                <input
                  value={search}
                  onChange={e => { setSearch(e.target.value); setPage(0) }}
                  placeholder="Buscar paciente, # auth…"
                  className="pl-8 pr-3 py-1.5 border border-gray-200 rounded-lg text-xs w-48 focus:border-azul-acento outline-none"
                />
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr>
                    {['Paciente','Aseguradora','Procedimiento','# Autorización','Estado','Fecha','Acciones'].map(h => (
                      <th key={h} className="px-3.5 py-2.5 text-left text-xs font-semibold text-gray-500 bg-gray-50 border-b border-gray-200 whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {slice.length === 0 && (
                    <tr><td colSpan={7} className="py-10 text-center text-sm text-gray-400">No hay autorizaciones con este filtro.</td></tr>
                  )}
                  {slice.map(a => (
                    <tr key={a.id} onClick={() => setSelected(a)} className="border-b border-gray-100 hover:bg-gray-50 cursor-pointer">
                      <td className="px-3.5 py-3">
                        <div className="flex items-center gap-2">
                          <div className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0" style={{ background: avatarColor(a.paciente_nombre) }}>
                            {iniciales(a.paciente_nombre)}
                          </div>
                          <div>
                            <div className="text-sm font-semibold text-gray-900">{a.paciente_nombre || 'Paciente'}</div>
                            <div className="text-xs text-gray-400">{capitalize(a.aseguradora || '')}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-3.5 py-3">
                        <span className={`text-sm font-semibold ${aseguraClass(a.aseguradora)}`}>{capitalize(a.aseguradora || '–')}</span>
                      </td>
                      <td className="px-3.5 py-3 max-w-[200px]">
                        <span className="text-sm text-gray-700 truncate block">{a.procedimiento_descripcion || '–'}</span>
                      </td>
                      <td className="px-3.5 py-3">
                        <span className="text-xs font-mono text-gray-700">{a.numero_autorizacion || '–'}</span>
                      </td>
                      <td className="px-3.5 py-3"><BadgeEstado estado={a.estado} /></td>
                      <td className="px-3.5 py-3 text-sm text-gray-500">{fmtDate(a.created_at)}</td>
                      <td className="px-3.5 py-3" onClick={e => e.stopPropagation()}>
                        <div className="flex items-center gap-1">
                          <button onClick={() => setSelected(a)} className="w-7 h-7 rounded-md bg-gray-100 hover:bg-gray-200 text-gray-500 flex items-center justify-center text-sm">👁</button>
                          {a.estado === 'pendiente_hitl' && (
                            <>
                              <button onClick={e => quickHITL(a.id, 'aprobar', e)} className="w-7 h-7 rounded-md bg-verde-bg hover:bg-green-200 text-verde-ok flex items-center justify-center text-sm" title="Aprobar">✓</button>
                              <button onClick={e => quickHITL(a.id, 'rechazar', e)} className="w-7 h-7 rounded-md bg-rojo-bg hover:bg-red-200 text-rojo flex items-center justify-center text-sm" title="Rechazar">✕</button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="px-4 py-3 flex items-center justify-between border-t border-gray-100">
              <span className="text-xs text-gray-400">
                {filtered.length === 0 ? '0 resultados' : `${page * PAGE_SIZE + 1}–${Math.min((page + 1) * PAGE_SIZE, filtered.length)} de ${filtered.length}`}
              </span>
              {pages > 1 && (
                <div className="flex gap-1">
                  <button disabled={page === 0} onClick={() => setPage(p => p - 1)} className="w-7 h-7 rounded-md border border-gray-200 text-xs flex items-center justify-center disabled:opacity-40 hover:bg-gray-100">‹</button>
                  {Array.from({ length: Math.min(pages, 7) }, (_, i) => (
                    <button key={i} onClick={() => setPage(i)} className={`w-7 h-7 rounded-md text-xs flex items-center justify-center border ${i === page ? 'bg-azul-acento text-white border-azul-acento' : 'border-gray-200 hover:bg-gray-100'}`}>{i + 1}</button>
                  ))}
                  <button disabled={page >= pages - 1} onClick={() => setPage(p => p + 1)} className="w-7 h-7 rounded-md border border-gray-200 text-xs flex items-center justify-center disabled:opacity-40 hover:bg-gray-100">›</button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <DetailDrawer autorizacion={selected} onClose={() => setSelected(null)} onRefresh={loadData} />
      <NewAuthModal open={modalOpen} onClose={() => setModalOpen(false)} onSuccess={loadData} />
    </>
  )
}
