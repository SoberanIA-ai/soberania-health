'use client'
import { useEffect, useState, useRef } from 'react'
import { Autorizacion, AuditLog } from '@/lib/types'
import { api } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import { useToast } from '@/contexts/ToastContext'
import { BadgeEstado } from '@/components/ui/Badge'
import { ConfidenceBar, confBarColor } from '@/components/ui/ConfidenceBar'
import { Spinner } from '@/components/ui/Spinner'
import { capitalize, fmtDateTime, fmtFileSize, iniciales, avatarColor } from '@/lib/utils'

interface Props {
  autorizacion: Autorizacion | null
  onClose: () => void
  onRefresh: () => void
}

interface HitlFile { name: string; size: number; type: string }

export function DetailDrawer({ autorizacion: a, onClose, onRefresh }: Props) {
  const { user } = useAuth()
  const { showToast } = useToast()
  const [audit, setAudit] = useState<AuditLog | null>(null)
  const [loading, setLoading] = useState(false)
  const [files, setFiles] = useState<HitlFile[]>([])
  const [notas, setNotas] = useState('')
  const [dragging, setDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!a) return
    setLoading(true)
    setAudit(null)
    setFiles([])
    setNotas('')
    api.getAudit(a.id).then(d => { setAudit(d); setLoading(false) })
  }, [a?.id])

  if (!a) return null

  const conf = a.confidence_score != null ? Math.round(a.confidence_score * 100) : null
  const isOpen = !!a

  async function aplicarHITL(decision: string) {
    if (!a) return
    const filesTag = files.length > 0
      ? `\n[Docs adjuntos (${files.length}): ${files.map(f => `${f.name} (${fmtFileSize(f.size)})`).join(', ')}]`
      : ''
    const notasFinal = (notas + filesTag).trim()
    const revisor = user?.email || 'dashboard_user'
    const r = await api.aplicarHITL(a.id, decision, revisor, notasFinal)
    if (!r) {
      showToast('error', 'Error de conexión', 'No se pudo contactar con el servidor. Inténtalo de nuevo.')
      return
    }
    if (!r.ok) {
      const d = await r.json()
      showToast('error', 'Error', d.detail || 'No se pudo aplicar.')
      return
    }
    const msgs: Record<string, string> = { aprobar: 'Caso aprobado.', rechazar: 'Caso rechazado.', mas_info: 'Se solicitó más información.' }
    showToast('success', 'HITL actualizado', msgs[decision] || '')
    onClose()
    onRefresh()
  }

  function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const newFiles = Array.from(e.target.files || [])
    setFiles(prev => {
      const merged = [...prev]
      newFiles.forEach(f => { if (!merged.find(x => x.name === f.name)) merged.push({ name: f.name, size: f.size, type: f.type }) })
      return merged
    })
    e.target.value = ''
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    const newFiles = Array.from(e.dataTransfer.files)
    setFiles(prev => {
      const merged = [...prev]
      newFiles.forEach(f => { if (!merged.find(x => x.name === f.name)) merged.push({ name: f.name, size: f.size, type: f.type }) })
      return merged
    })
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 bg-black/30 z-[100] transition-opacity ${isOpen ? 'block' : 'hidden'}`}
        onClick={onClose}
      />
      {/* Drawer */}
      <div className={`fixed top-0 right-0 w-[560px] max-w-[95vw] h-screen bg-white z-[101] shadow-2xl flex flex-col transition-transform duration-250 ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
        {/* Header */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-200 sticky top-0 bg-white z-10">
          <h2 className="text-base font-bold flex-1">Autorización · {a.numero_autorizacion || a.id.slice(0, 8)}</h2>
          <BadgeEstado estado={a.estado} />
          <button onClick={onClose} className="w-7 h-7 rounded-md bg-gray-100 hover:bg-gray-200 flex items-center justify-center text-sm">✕</button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">

          {/* Datos del caso */}
          <section>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Datos del caso</h3>
            <div className="bg-gray-50 rounded-xl p-4 border border-gray-100 space-y-2">
              {[
                ['Paciente', a.paciente_nombre || '–'],
                ['Aseguradora', capitalize(a.aseguradora || '–')],
                ['Póliza', [a.poliza_numero, a.poliza_tipo ? `(${a.poliza_tipo})` : ''].filter(Boolean).join(' ') || '–'],
                ['Procedimiento', a.procedimiento_descripcion || '–'],
                ['CIE-10', a.procedimiento_cie10 || '–'],
                ['Médico', a.medico_nombre || '–'],
                ['Urgente', a.urgencia === 'urgente' ? '🚨 Sí' : 'No'],
                ['Fecha solicitud', fmtDateTime(a.created_at)],
              ].map(([k, v]) => (
                <div key={k} className="flex gap-2">
                  <span className="text-xs text-gray-500 min-w-[130px] pt-0.5">{k}</span>
                  <span className="text-sm font-medium text-gray-900 flex-1">{v}</span>
                </div>
              ))}
              {conf !== null && (
                <div className="flex gap-2">
                  <span className="text-xs text-gray-500 min-w-[130px] pt-1">Confidence</span>
                  <ConfidenceBar value={a.confidence_score} maxWidth={120} />
                </div>
              )}
              {a.numero_autorizacion && (
                <div className="flex gap-2">
                  <span className="text-xs text-gray-500 min-w-[130px]"># Autorización</span>
                  <span className="text-sm font-bold font-mono">{a.numero_autorizacion}</span>
                </div>
              )}
            </div>
          </section>

          {/* Rechazo Panel */}
          {(a.estado === 'denegado' || a.estado === 'rechazado_hitl') && (
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Motivo del Rechazo</h3>
              <div className="bg-rojo-bg border border-rojo/30 rounded-xl p-4">
                <div className="text-sm font-bold text-rojo mb-2">✕ Solicitud rechazada</div>
                <div className="text-sm text-gray-700">
                  {a.estado === 'denegado' 
                    ? (a.motivo_denegacion || 'La aseguradora ha denegado la solicitud sin especificar motivo.')
                    : (a.hitl_notas || 'Rechazado por el supervisor médico sin añadir notas específicas.')}
                </div>
              </div>
            </section>
          )}

          {/* HITL Panel */}
          {a.estado === 'pendiente_hitl' && (
            <section>
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Revisión HITL requerida</h3>
              <div className="bg-amber-50 border border-yellow-200 rounded-xl p-4">
                <div className="text-sm font-bold text-amber-800 mb-2">⚠️ Este caso requiere revisión humana</div>
                <div className="text-sm text-amber-900 bg-amber-100/50 px-3 py-2 rounded-lg mb-3 border border-amber-200/50">
                  <span className="font-semibold block mb-0.5">Mensaje del Agente IA:</span>
                  {a.razon_hitl || 'El sistema de IA ha marcado este caso para revisión.'}
                </div>
                <div className="text-xs text-gray-600 bg-white px-3 py-2 rounded-lg mb-3">
                  Confidence del agente: {conf !== null ? `${conf}%` : 'N/D'} (umbral HITL: &lt;80%)
                </div>

                {/* Notes */}
                <label className="text-xs font-medium text-gray-500 mb-1.5 block">Notas del revisor (opcional)</label>
                <textarea
                  value={notas}
                  onChange={e => setNotas(e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg resize-none min-h-[60px] font-sans focus:border-azul-acento outline-none"
                  placeholder="Observaciones…"
                />

                {/* File upload */}
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1.5">📎 Documentación adjunta</div>
                <div
                  className={`border-2 border-dashed rounded-lg p-3 text-center cursor-pointer transition-colors ${dragging ? 'border-azul-acento bg-azul-claro' : 'border-gray-300 hover:border-azul-acento hover:bg-azul-claro'}`}
                  onClick={() => fileInputRef.current?.click()}
                  onDragOver={e => { e.preventDefault(); setDragging(true) }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={onDrop}
                >
                  <input ref={fileInputRef} type="file" multiple className="hidden" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.xml" onChange={onFileChange} />
                  <div className="text-xs text-gray-500">
                    <strong className="text-azul-acento">Haz clic o arrastra archivos</strong><br />
                    PDF, Word, imágenes, XML
                  </div>
                </div>

                {files.length > 0 && (
                  <div className="mt-1.5 flex flex-col gap-1">
                    {files.map(f => {
                      const icon = f.type.startsWith('image') ? '🖼️' : f.name.endsWith('.pdf') ? '📄' : f.name.match(/\.docx?$/) ? '📝' : '📎'
                      return (
                        <div key={f.name} className="flex items-center gap-2 px-2.5 py-1.5 bg-white border border-gray-200 rounded-lg text-xs">
                          <span>{icon}</span>
                          <span className="flex-1 font-medium truncate">{f.name}</span>
                          <span className="text-gray-400 shrink-0">{fmtFileSize(f.size)}</span>
                          <button onClick={() => setFiles(prev => prev.filter(x => x.name !== f.name))} className="text-rojo hover:opacity-70 pl-1">✕</button>
                        </div>
                      )
                    })}
                  </div>
                )}

                {/* HITL buttons */}
                <div className="flex gap-2 mt-3">
                  <button onClick={() => aplicarHITL('aprobar')} className="flex-1 py-2 bg-verde-ok text-white text-sm font-semibold rounded-lg hover:bg-green-700 transition-colors">✓ Aprobar</button>
                  <button onClick={() => aplicarHITL('mas_info')} className="flex-1 py-2 bg-naranja-bg text-naranja border border-yellow-300 text-sm font-semibold rounded-lg hover:bg-amber-100 transition-colors">ℹ Más info</button>
                  <button onClick={() => aplicarHITL('rechazar')} className="flex-1 py-2 bg-rojo text-white text-sm font-semibold rounded-lg hover:bg-red-700 transition-colors">✕ Rechazar</button>
                </div>
              </div>
            </section>
          )}

          {/* Audit trail */}
          <section>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Audit log · Trazabilidad SHA256</h3>
            {loading && <div className="flex items-center gap-2 py-4"><Spinner /><span className="text-sm text-gray-500">Cargando…</span></div>}
            {!loading && audit && (
              <>
                {audit.integro
                  ? <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-verde-bg text-verde-ok text-sm font-semibold">✓ Cadena SHA256 íntegra</span>
                  : <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rojo-bg text-rojo text-sm font-semibold">⚠ Integridad comprometida</span>
                }
                <div className="mt-3 relative pl-6 before:content-[''] before:absolute before:left-2 before:top-0 before:bottom-0 before:w-0.5 before:bg-gray-200">
                  {audit.entries.map((e, i) => {
                    const tipo = e.actor?.includes('llm') ? 'llm' : e.hitl_intervencion ? 'human' : 'python'
                    const dotColor = tipo === 'llm' ? '#8b5cf6' : tipo === 'human' ? '#16a34a' : '#0ea5e9'
                    const tipoBadge = tipo === 'llm' ? '🤖 LLM' : tipo === 'human' ? '👤 Humano' : '🐍 Python'
                    const ts = e.timestamp ? new Date(e.timestamp).toLocaleTimeString('es-ES') : ''
                    return (
                      <div key={i} className="relative mb-4">
                        <div className="absolute -left-[22px] top-1 w-3.5 h-3.5 rounded-full border-2 border-white" style={{ background: dotColor, boxShadow: `0 0 0 2px #e5e7eb` }} />
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-sm font-semibold text-gray-900">{e.accion}</span>
                          <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-full">{tipoBadge}</span>
                          <span className="text-xs text-gray-400">{ts}</span>
                        </div>
                        <div className="bg-gray-50 rounded-lg px-3 py-2 border border-gray-100">
                          {e.datos_salida?.razon_decision != null && <div className="text-xs text-gray-700 mb-1">{String(e.datos_salida.razon_decision)}</div>}
                          {e.confidence_score != null && <div className="text-xs text-gray-500 font-mono">Confidence: {Math.round(e.confidence_score * 100)}%</div>}
                          <div className="text-xs text-gray-400 font-mono">SHA256: {e.hash_sha256 ? e.hash_sha256.slice(0, 16) + '…' : '–'}</div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </>
            )}
            {!loading && !audit && <div className="text-sm text-gray-400">No disponible</div>}
          </section>
        </div>
      </div>
    </>
  )
}
