export interface Autorizacion {
  id: string
  created_at: string
  updated_at: string
  paciente_nombre?: string
  medico_nombre?: string
  procedimiento_descripcion?: string
  procedimiento_cie10?: string
  urgencia: string
  aseguradora?: string
  poliza_numero?: string
  poliza_tipo?: string
  confidence_score?: number
  estado: string
  modo: string
  numero_autorizacion?: string
  hitl_requerido: boolean
  hitl_revisado_at?: string
  hitl_revisor?: string
  hitl_decision?: string
  hitl_notas?: string
}

export interface Metricas {
  total: number
  automatizadas: number
  con_hitl: number
  pendientes_hitl: number
  autorizadas: number
  denegadas: number
  tasa_automatizacion: number
}

export interface MetricasAIAct {
  total_autorizaciones: number
  con_supervision_humana: number
  porcentaje_supervision: number
  decisiones_humanas_registradas: number
  humano_contradijo_agente: number
  porcentaje_contradicciones: number
  tiempo_medio_revision_segundos?: number
}

export interface AuditEntry {
  accion: string
  actor: string
  timestamp: string
  resultado: string
  confidence_score?: number
  hash_sha256?: string
  hitl_intervencion: boolean
  datos_salida?: Record<string, unknown>
}

export interface AuditLog {
  autorizacion_id: string
  integro: boolean
  entries: AuditEntry[]
}

export interface AIActPaso {
  accion: string
  tipo: string
  timestamp: string
  razon_decision?: string
  confidence_score?: number
  hash_sha256?: string
  datos_entrada?: Record<string, unknown>
  datos_salida?: Record<string, unknown>
}

export interface AIActReport {
  autorizacion: {
    id: string
    paciente_nombre?: string
    estado_final: string
    confidence_score?: number
    numero_autorizacion?: string
    tiempo_total_segundos?: number
  }
  audit: {
    integro: boolean
    pasos: AIActPaso[]
  }
  intervencion_humana?: {
    revisor_nombre: string
    decision_humana: string
    coincide_con_agente: boolean
  }
}

export interface Usuario {
  id: string
  email: string
  nombre: string
  rol: string
}

export interface Toast {
  id: string
  tipo: 'success' | 'warning' | 'info' | 'error'
  titulo: string
  msg?: string
}
