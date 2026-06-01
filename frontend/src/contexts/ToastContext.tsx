'use client'
import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { Toast } from '@/lib/types'

interface ToastCtx {
  toasts: Toast[]
  showToast: (tipo: Toast['tipo'], titulo: string, msg?: string) => void
  removeToast: (id: string) => void
}

const ToastContext = createContext<ToastCtx>({
  toasts: [], showToast: () => {}, removeToast: () => {},
})

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const showToast = useCallback((tipo: Toast['tipo'], titulo: string, msg?: string) => {
    const id = Math.random().toString(36).slice(2)
    setToasts(prev => [...prev.slice(-2), { id, tipo, titulo, msg }])
    setTimeout(() => removeToast(id), 5000)
  }, [removeToast])

  return (
    <ToastContext.Provider value={{ toasts, showToast, removeToast }}>
      {children}
      <ToastContainer />
    </ToastContext.Provider>
  )
}

function ToastContainer() {
  const { toasts, removeToast } = useContext(ToastContext)
  const icons = { success: '✅', warning: '⏳', info: 'ℹ️', error: '❌' }
  const borders = { success: 'border-verde-ok', warning: 'border-amarillo', info: 'border-azul-acento', error: 'border-rojo' }

  return (
    <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2 max-w-xs">
      {toasts.map(t => (
        <div key={t.id} className={`flex items-start gap-2 p-3 bg-white rounded-xl shadow-lg border-l-4 ${borders[t.tipo]} animate-slide-in`}>
          <span className="text-base shrink-0 mt-0.5">{icons[t.tipo]}</span>
          <div className="flex-1">
            <div className="text-sm font-semibold text-gray-900">{t.titulo}</div>
            {t.msg && <div className="text-xs text-gray-500 mt-0.5">{t.msg}</div>}
          </div>
          <button onClick={() => removeToast(t.id)} className="text-gray-400 hover:text-gray-700 text-sm leading-none">✕</button>
        </div>
      ))}
    </div>
  )
}

export function useToast() { return useContext(ToastContext) }
