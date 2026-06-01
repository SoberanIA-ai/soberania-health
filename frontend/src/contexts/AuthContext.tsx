'use client'
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { Usuario } from '@/lib/types'

interface AuthCtx {
  user: Usuario | null
  token: string | null
  login: (token: string, user: Usuario) => void
  logout: () => void
}

const AuthContext = createContext<AuthCtx>({
  user: null, token: null, login: () => {}, logout: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Usuario | null>(null)
  const [token, setToken] = useState<string | null>(null)

  useEffect(() => {
    const t = localStorage.getItem('soberania_token')
    const u = localStorage.getItem('soberania_user')
    if (t && u) {
      try { setUser(JSON.parse(u)); setToken(t) } catch { logout() }
    }
    window.addEventListener('soberania:logout', logout)
    return () => window.removeEventListener('soberania:logout', logout)
  }, [])

  function login(t: string, u: Usuario) {
    localStorage.setItem('soberania_token', t)
    localStorage.setItem('soberania_user', JSON.stringify(u))
    setToken(t)
    setUser(u)
  }

  function logout() {
    localStorage.removeItem('soberania_token')
    localStorage.removeItem('soberania_user')
    setToken(null)
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, token, login, logout }}>{children}</AuthContext.Provider>
}

export function useAuth() { return useContext(AuthContext) }
