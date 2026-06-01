'use client'
import { useState } from 'react'
import { api } from '@/lib/api'
import { Spinner } from '@/components/ui/Spinner'
import { estadoLabel } from '@/components/ui/Badge'

interface Props {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

export function NewAuthModal({ open, onClose, onSuccess }: Props) {
  const [form, setForm] = useState({ paciente: '', aseguradora: '', poliza: '', procedimiento: '', medico: '', urgente: false, notas: '' })
  const [result, setResult] = useState<{ tipo: string; msg: string } | null>(null)
  const [loading, setLoading] = useState(false)

  if (!open) return null

  function set(k: keyof typeof form, v: string | boolean) {
    setForm(prev => ({ ...prev, [k]: v }))
  }

  async function enviar() {
    if (!form.paciente || !form.aseguradora || !form.poliza || !form.procedimiento || !form.medico) {
      setResult({ tipo: 'error', msg: 'Completa todos los campos obligatorios (*).' })
      return
    }
    const orden = `Paciente: ${form.paciente}\nAseguradora: ${form.aseguradora}\nPóliza: ${form.poliza}\nProcedimiento: ${form.procedimiento}${form.urgente ? ' URGENTE' : ''}\nMédico: ${form.medico}${form.notas ? '\nNotas: ' + form.notas : ''}`
    setLoading(true)
    try {
      const r = await api.procesar(orden)
      if (!r) return
      const data = await r.json()
      if (!r.ok) { setResult({ tipo: 'error', msg: data.detail || 'Error procesando.' }); return }
      const tipo = data.estado === 'autorizado' ? 'success' : data.estado === 'pendiente_hitl' ? 'hitl' : 'error'
      const conf = data.confidence_score != null ? ` · Confidence: ${Math.round(data.confidence_score * 100)}%` : ''
      setResult({ tipo, msg: `Estado: ${estadoLabel(data.estado)}${conf}${data.numero_autorizacion ? ' · #' + data.numero_autorizacion : ''}` })
      onSuccess()
    } catch { setResult({ tipo: 'error', msg: 'Error de red.' }) }
    finally { setLoading(false) }
  }

  const resultBg = { success: 'bg-verde-bg text-verde-ok', hitl: 'bg-amarillo-bg text-amarillo', error: 'bg-rojo-bg text-rojo' }

  return (
    <div className="fixed inset-0 bg-black/45 z-[200] flex items-center justify-center" onClick={e => { if (e.target === e.currentTarget) onClose() }}>
      <div className="bg-white rounded-2xl p-7 w-full max-w-[520px] max-h-[90vh] overflow-y-auto shadow-2xl">
        <h2 className="text-lg font-bold mb-5">Nueva autorización</h2>

        {[
          { label: 'Nombre del paciente *', key: 'paciente', placeholder: 'Ej: María García López' },
          { label: 'Número de póliza *', key: 'poliza', placeholder: 'Ej: 1234567' },
          { label: 'Procedimiento solicitado *', key: 'procedimiento', placeholder: 'Ej: Resonancia magnética rodilla derecha' },
          { label: 'Médico solicitante *', key: 'medico', placeholder: 'Ej: Dr. Juan Pérez Traumatología' },
        ].map(f => (
          <div key={f.key} className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1.5">{f.label}</label>
            <input
              type="text"
              value={form[f.key as keyof typeof form] as string}
              onChange={e => set(f.key as keyof typeof form, e.target.value)}
              placeholder={f.placeholder}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-azul-acento outline-none font-sans"
            />
          </div>
        ))}

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Aseguradora *</label>
          <select value={form.aseguradora} onChange={e => set('aseguradora', e.target.value)} className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:border-azul-acento outline-none font-sans">
            <option value="">Seleccionar aseguradora…</option>
            <option value="Sanitas">Sanitas</option>
            <option value="Adeslas">Adeslas / SegurCaixa</option>
            <option value="DKV">DKV Seguros</option>
            <option value="Otra">Otra → HITL automático</option>
          </select>
        </div>

        <div className="mb-4 flex items-center gap-2">
          <input type="checkbox" id="form-urgente" checked={form.urgente} onChange={e => set('urgente', e.target.checked)} className="w-4 h-4 accent-azul-acento cursor-pointer" />
          <label htmlFor="form-urgente" className="text-sm cursor-pointer">Urgente</label>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Notas adicionales</label>
          <textarea value={form.notas} onChange={e => set('notas', e.target.value)} placeholder="Información clínica adicional (opcional)" className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-y min-h-[70px] focus:border-azul-acento outline-none font-sans" />
        </div>

        {result && (
          <div className={`p-3 rounded-lg text-sm mb-4 ${resultBg[result.tipo as keyof typeof resultBg] || 'bg-gray-100'}`}>
            {result.msg}
          </div>
        )}

        <div className="flex gap-2.5 justify-end">
          <button onClick={onClose} className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">Cancelar</button>
          <button onClick={enviar} disabled={loading} className="px-5 py-2 bg-azul-acento text-white rounded-lg text-sm font-semibold disabled:opacity-60 hover:bg-blue-700 flex items-center gap-2">
            {loading && <Spinner size={14} />} Enviar al agente
          </button>
        </div>
      </div>
    </div>
  )
}
