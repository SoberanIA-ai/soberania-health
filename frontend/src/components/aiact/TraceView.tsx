'use client'
import { useState } from 'react'
import { Autorizacion, AIActReport } from '@/lib/types'
import { api } from '@/lib/api'
import { BadgeEstado } from '@/components/ui/Badge'
import { Spinner } from '@/components/ui/Spinner'

interface Props {
  autorizacion: Autorizacion
  onClose: () => void
}

export function TraceView({ autorizacion: a, onClose }: Props) {
  const [report, setReport] = useState<AIActReport | null>(null)
  const [loading, setLoading] = useState(false)

  async function loadReport() {
    if (report || loading) return
    setLoading(true)
    const r = await api.getAIActReport(a.id)
    setReport(r)
    setLoading(false)
  }

  if (!report && !loading) loadReport()

  async function exportar() {
    const r = await api.getAIActReport(a.id)
    if (!r) return
    const blob = new Blob([JSON.stringify(r, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url; link.download = `aiact-report-${a.id.slice(0, 8)}.json`
    document.body.appendChild(link); link.click(); document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 mt-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-bold">
          Trazabilidad · {a.id.slice(0, 8)}… · {a.paciente_nombre || ''}
        </h3>
        <div className="flex gap-2">
          <button onClick={exportar} className="px-3 py-1.5 bg-azul-acento text-white text-xs font-semibold rounded-lg hover:bg-blue-700">⬇ Exportar JSON</button>
          <button onClick={onClose} className="px-3 py-1.5 bg-gray-100 text-gray-600 text-xs font-semibold rounded-lg hover:bg-gray-200">✕ Cerrar</button>
        </div>
      </div>

      {loading && <div className="flex items-center gap-2 py-4"><Spinner /><span className="text-sm text-gray-500">Cargando trazabilidad…</span></div>}

      {report && (
        <>
          {/* Summary */}
          <div className="bg-gray-50 rounded-xl p-4 border border-gray-100 space-y-2 mb-4">
            {[
              ['Estado final', <BadgeEstado key="e" estado={report.autorizacion.estado_final} />],
              ['Confidence', report.autorizacion.confidence_score != null ? `${Math.round(report.autorizacion.confidence_score * 100)}%` : '–'],
              ['Tiempo total', report.autorizacion.tiempo_total_segundos != null ? `${report.autorizacion.tiempo_total_segundos.toFixed(2)}s` : '–'],
              ...(report.autorizacion.numero_autorizacion ? [['# Autorización', <span key="n" className="font-mono font-bold">{report.autorizacion.numero_autorizacion}</span>]] : []),
            ].map(([k, v], i) => (
              <div key={i} className="flex gap-2">
                <span className="text-xs text-gray-500 min-w-[130px] pt-0.5">{k}</span>
                <span className="text-sm font-medium text-gray-900">{v as React.ReactNode}</span>
              </div>
            ))}
          </div>

          {/* Human intervention */}
          {report.intervencion_humana && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-4 space-y-2">
              <div className="text-sm font-bold mb-2">Intervención humana</div>
              {[
                ['Revisor', report.intervencion_humana.revisor_nombre],
                ['Decisión', report.intervencion_humana.decision_humana],
                ['¿Coincide con agente?', report.intervencion_humana.coincide_con_agente ? '✅ Sí' : '⚠️ No'],
              ].map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <span className="text-xs text-gray-500 min-w-[130px]">{k}</span>
                  <span className="text-sm font-medium">{v}</span>
                </div>
              ))}
            </div>
          )}

          {/* Timeline */}
          <div className="relative pl-6 before:content-[''] before:absolute before:left-2 before:top-0 before:bottom-0 before:w-0.5 before:bg-gray-200">
            {report.audit.pasos.map((p, i) => {
              const tipo = p.tipo || 'python'
              const dotColor = tipo === 'llm' ? '#8b5cf6' : tipo === 'human' ? '#16a34a' : '#0ea5e9'
              const tipoBadge = tipo === 'llm' ? '🤖 LLM' : tipo === 'human' ? '👤 Humano' : '🐍 Python'
              const ts = p.timestamp ? new Date(p.timestamp).toLocaleString('es-ES') : ''
              return (
                <div key={i} className="relative mb-4">
                  <div className="absolute -left-[22px] top-1 w-3.5 h-3.5 rounded-full border-2 border-white" style={{ background: dotColor, boxShadow: '0 0 0 2px #e5e7eb' }} />
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-gray-900">{p.accion}</span>
                    <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">{tipoBadge}</span>
                    <span className="text-xs text-gray-400">{ts}</span>
                  </div>
                  <div className="bg-gray-50 rounded-lg px-3 py-2 border border-gray-100">
                    {p.razon_decision && <div className="text-xs text-gray-700 mb-1">{p.razon_decision}</div>}
                    {p.confidence_score != null && <div className="text-xs text-gray-500 font-mono">Confidence: {Math.round(p.confidence_score * 100)}%</div>}
                    {p.hash_sha256 && <div className="text-xs text-gray-400 font-mono">SHA256: {p.hash_sha256}</div>}
                    {(p.datos_entrada || p.datos_salida) && (
                      <details className="mt-1">
                        <summary className="text-xs text-azul-acento cursor-pointer">Ver datos entrada/salida</summary>
                        <pre className="text-[10px] text-gray-700 mt-1 whitespace-pre-wrap break-all max-h-[120px] overflow-y-auto bg-white p-1.5 rounded border border-gray-100">
                          {JSON.stringify({ entrada: p.datos_entrada, salida: p.datos_salida }, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Integrity */}
          <div className="mt-3">
            {report.audit.integro
              ? <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-verde-bg text-verde-ok text-sm font-semibold">✓ Sistema compliant con AI Act · Cadena íntegra</span>
              : <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rojo-bg text-rojo text-sm font-semibold">⚠ Integridad comprometida</span>
            }
          </div>
        </>
      )}
    </div>
  )
}
