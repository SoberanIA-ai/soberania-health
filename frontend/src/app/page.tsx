'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { api } from '@/lib/api'
import { Spinner } from '@/components/ui/Spinner'

export default function LoginPage() {
  const { user, login } = useAuth()
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) {
      if (user.rol === 'auditor') router.replace('/auditoria')
      else router.replace('/dashboard')
    }
  }, [user, router])

  async function handleLogin() {
    if (!email || !password) { setError('Completa todos los campos.'); return }
    setLoading(true)
    setError('')
    try {
      const r = await api.login(email, password)
      const data = await r.json()
      if (!r.ok) { setError(data.detail || 'Credenciales incorrectas.'); return }
      login(data.access_token, data.usuario)
      if (data.usuario.rol === 'auditor') {
        router.replace('/auditoria')
      } else {
        router.replace('/dashboard')
      }
    } catch {
      setError('Error de conexión. ¿Está el servidor levantado?')
    } finally {
      setLoading(false)
    }
  }

  function onKey(e: React.KeyboardEvent) {
    if (e.key === 'Enter') handleLogin()
  }

  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #0F1C2E 0%, #1e3a5f 100%)' }}>
      <div className="bg-white rounded-2xl p-10 w-full max-w-[420px] shadow-2xl">
        <div className="text-center mb-7">
          <div className="text-4xl mb-2">🏥</div>
          <div className="text-xl font-bold text-azul-marino">HM Hospitales · SoberanIA Health</div>
          <div className="text-sm text-gray-500 mt-1">Portal de Autorizaciones Médicas</div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Correo electrónico</label>
          <input
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyDown={onKey}
            placeholder="usuario@hmhospitales.es"
            autoComplete="username"
            className="w-full px-3.5 py-2.5 border-[1.5px] border-gray-200 rounded-lg text-sm focus:border-azul-acento focus:ring-2 focus:ring-blue-100 outline-none transition font-sans"
          />
        </div>

        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Contraseña</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyDown={onKey}
            placeholder="••••••••"
            autoComplete="current-password"
            className="w-full px-3.5 py-2.5 border-[1.5px] border-gray-200 rounded-lg text-sm focus:border-azul-acento focus:ring-2 focus:ring-blue-100 outline-none transition font-sans"
          />
        </div>

        {error && <div className="text-rojo text-sm text-center mb-4">{error}</div>}

        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full py-3 bg-azul-acento text-white rounded-lg text-[15px] font-semibold disabled:opacity-60 hover:bg-blue-700 transition flex items-center justify-center gap-2 font-sans"
        >
          {loading ? <><Spinner size={16} /> Entrando…</> : 'Entrar'}
        </button>
      </div>
    </div>
  )
}
