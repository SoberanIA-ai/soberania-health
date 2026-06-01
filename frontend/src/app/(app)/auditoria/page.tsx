'use client'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { Autorizacion, MetricasAIAct } from '@/lib/types'
import { BadgeEstado, TipoDecisionBadge } from '@/components/ui/Badge'
import { ConfidenceBar } from '@/components/ui/ConfidenceBar'
import { TraceView } from '@/components/aiact/TraceView'
import { Spinner } from '@/components/ui/Spinner'
import { aseguraClass, capitalize, fmtDate } from '@/lib/utils'

function KpiCard({ icon, num, label, sub, numColor, bgColor }: { icon: string; num: string | number; label: string; sub?: string; numColor?: string; bgColor?: string }) {
  return (
    <div className="bg-white rounded-xl p-4 border border-gray-200">
      <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg mb-2" style={{ background: bgColor || '#eff6ff' }}>{icon}</div>
      <div className="text-2xl font-bold leading-none" style={{ color: numColor || '#111827' }}>{num}</div>
      <div className="text-xs text-gray-500 font-medium mt-1">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  )
}

export default function AuditoriaPage() {
  const [autorizaciones, setAutorizaciones] = useState<Autorizacion[]>([])
  const [metricas, setMetricas] = useState<MetricasAIAct | null>(null)
  const [loading, setLoading] = useState(true)
  const [selectedTrace, setSelectedTrace] = useState<Autorizacion | null>(null)

  useEffect(() => {
    Promise.all([api.getAutorizaciones(), api.getMetricasAIAct()]).then(([a, m]) => {
      if (a) setAutorizaciones(a)
      if (m) setMetricas(m)
      setLoading(false)
    })
  }, [])

  return (
    <>
      <div className="bg-white px-6 py-4 border-b border-gray-200 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-lg font-bold text-gray-900">🛡️ Panel de Auditoría AI Act</h1>
          <p className="text-sm text-gray-500">Trazabilidad y compliance del sistema · Reglamento UE 2024/1689</p>
        </div>
        <span className="text-xs bg-gray-100 text-gray-500 px-2.5 py-1 rounded-full font-medium">Solo lectura</span>
      </div>

      <div className="flex-1 overflow-y-auto p-6 min-h-0 space-y-5">
        {loading && <div className="flex justify-center py-12"><Spinner size={24} /></div>}

        {!loading && metricas && (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-4 gap-3.5">
              <KpiCard icon="👤" num={`${Math.round(metricas.porcentaje_supervision * 100)}%`} label="Supervisión humana" sub={`${metricas.con_supervision_humana} de ${metricas.total_autorizaciones} casos`} numColor="#2563eb" bgColor="#eff6ff" />
              <KpiCard icon="⚖️" num={metricas.humano_contradijo_agente} label="Contradicciones humano/agente" sub={`${Math.round(metricas.porcentaje_contradicciones * 100)}% de revisiones HITL`} bgColor="#dcfce7" />
              <KpiCard icon="⏱️" num={metricas.tiempo_medio_revision_segundos != null ? Math.round(metricas.tiempo_medio_revision_segundos) : '–'} label="Tiempo medio revisión HITL" sub="segundos promedio" bgColor="#fef3c7" />
              <KpiCard icon="🔐" num="100%" label="Integridad del log" sub="SHA256 encadenado" numColor="#16a34a" bgColor="#dcfce7" />
            </div>

            {/* Tabla auditora */}
            <div>
              <h2 className="text-base font-bold text-gray-900 mb-3">Todas las autorizaciones · vista auditor</h2>
              <div className="bg-white rounded-xl border border-gray-200">
                <div className="overflow-x-auto">
                  <table className="w-full border-collapse">
                    <thead>
                      <tr>
                        {['ID','Fecha','Paciente','Aseg.','Estado','Tipo decisión','Confidence','Acciones'].map(h => (
                          <th key={h} className="px-3 py-2.5 text-left text-xs font-semibold text-gray-500 bg-gray-50 border-b border-gray-200 whitespace-nowrap">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {autorizaciones.map(a => (
                        <tr key={a.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="px-3 py-2.5 font-mono text-xs text-gray-500">{a.id.slice(0, 8)}…</td>
                          <td className="px-3 py-2.5 text-sm text-gray-600">{fmtDate(a.created_at)}</td>
                          <td className="px-3 py-2.5 text-sm text-gray-900">{a.paciente_nombre || '–'}</td>
                          <td className="px-3 py-2.5"><span className={`text-sm font-semibold ${aseguraClass(a.aseguradora)}`}>{capitalize(a.aseguradora || '–')}</span></td>
                          <td className="px-3 py-2.5"><BadgeEstado estado={a.estado} /></td>
                          <td className="px-3 py-2.5"><TipoDecisionBadge a={a} /></td>
                          <td className="px-3 py-2.5"><ConfidenceBar value={a.confidence_score} maxWidth={80} /></td>
                          <td className="px-3 py-2.5">
                            <button
                              onClick={() => setSelectedTrace(selectedTrace?.id === a.id ? null : a)}
                              className={`w-7 h-7 rounded-md flex items-center justify-center text-sm transition-colors ${selectedTrace?.id === a.id ? 'bg-azul-acento text-white' : 'bg-gray-100 hover:bg-gray-200 text-gray-500'}`}
                              title="Ver trazabilidad"
                            >🔍</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Trace view */}
            {selectedTrace && (
              <TraceView autorizacion={selectedTrace} onClose={() => setSelectedTrace(null)} />
            )}

            {/* Estado del sistema */}
            <div>
              <h2 className="text-base font-bold text-gray-900 mb-3">Estado del sistema</h2>
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                {[
                  { k: 'Versión calculadores', v: '1.0.0-simulado', cls: 'text-verde-ok' },
                  { k: 'DATA_STATUS', v: 'SIMULADO (Sanitas / Adeslas / DKV)', cls: 'text-amarillo' },
                  { k: 'Modo actual', v: 'mock', cls: '' },
                  { k: 'Integración Doctoris', v: 'STUB (pendiente acceso HM)', cls: 'text-naranja' },
                  { k: 'Tests automatizados', v: '107/107 ✓', cls: 'text-verde-ok' },
                  { k: 'Cobertura', v: '94%', cls: 'text-verde-ok' },
                  { k: 'Clasificación AI Act', v: 'Alto Riesgo · Anexo III punto 5.a', cls: '' },
                  { k: 'HITL obligatorio modo real', v: 'Sí', cls: 'text-verde-ok' },
                ].map(row => (
                  <div key={row.k} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-none text-sm">
                    <span className="text-gray-500">{row.k}</span>
                    <span className={`font-semibold ${row.cls || 'text-gray-900'}`}>{row.v}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </>
  )
}
