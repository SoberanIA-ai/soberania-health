import { Autorizacion } from '@/lib/types'

const ESTADO_LABEL: Record<string, string> = {
  pendiente_hitl: 'Pendiente HITL',
  autorizado: 'Autorizada',
  denegado: 'Rechazada',
  aprobado_hitl: 'Aprobado HITL',
  rechazado_hitl: 'Rechazado HITL',
  informacion_adicional_requerida: 'Más info',
  en_proceso: 'En proceso',
  recibido: 'Recibido',
  error: 'Error',
  error_procesamiento: 'Error de procesamiento',
}

const ESTADO_CLASS: Record<string, string> = {
  autorizado:      'bg-verde-bg text-verde-ok',
  aprobado_hitl:   'bg-verde-bg text-verde-ok',
  pendiente_hitl:  'bg-amarillo-bg text-amarillo',
  informacion_adicional_requerida: 'bg-amarillo-bg text-amarillo',
  denegado:        'bg-rojo-bg text-rojo',
  rechazado_hitl:  'bg-rojo-bg text-rojo',
  en_proceso:      'bg-naranja-bg text-naranja',
  recibido:        'bg-naranja-bg text-naranja',
  error:           'bg-rojo-bg text-red-900',
  error_procesamiento: 'bg-rojo-bg text-red-900',
}

export function estadoLabel(e: string) {
  return ESTADO_LABEL[e] || e.charAt(0).toUpperCase() + e.slice(1)
}

export function estadoColor(e: string): string {
  const m: Record<string, string> = {
    pendiente_hitl: '#ca8a04', autorizado: '#16a34a', denegado: '#dc2626',
    aprobado_hitl: '#16a34a', rechazado_hitl: '#dc2626',
    en_proceso: '#d97706', recibido: '#d97706', error: '#7f1d1d',
    error_procesamiento: '#7f1d1d',
  }
  return m[e] || '#9ca3af'
}

export function BadgeEstado({ estado }: { estado: string }) {
  const cls = ESTADO_CLASS[estado] || 'bg-gray-100 text-gray-500'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap ${cls}`}>
      {estadoLabel(estado)}
    </span>
  )
}

export function TipoDecisionBadge({ a }: { a: Autorizacion }) {
  if (!a.hitl_requerido) return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-700">🤖 Automático</span>
  if (a.hitl_decision === 'aprobar')  return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-verde-bg text-verde-ok">👤 HITL: Aprobado</span>
  if (a.hitl_decision === 'rechazar') return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-rojo-bg text-rojo">👤 HITL: Rechazado</span>
  if (a.hitl_decision === 'mas_info') return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amarillo-bg text-amarillo">👤 HITL: Más info</span>
  return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-amarillo-bg text-amarillo">⏳ HITL: Pendiente</span>
}
