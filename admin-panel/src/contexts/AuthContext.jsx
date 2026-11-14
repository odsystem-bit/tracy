import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { authApi } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('admin_token')
    if (!token) {
      setLoading(false)
      return
    }
    // Nettoyer les anciens tokens démo
    if (token.startsWith('demo_token_')) {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
      setLoading(false)
      return
    }
    try {
      const { data } = await authApi.me()
      setUser(data)
    } catch {
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_user')
    }
    setLoading(false)
  }, [])

  useEffect(() => {
    // Safety: toujours arrêter le loading après 5s
    const safety = setTimeout(() => setLoading(false), 5000)
    checkAuth()
    return () => clearTimeout(safety)
  }, [checkAuth])

  const login = async (email, password) => {
    const { data } = await authApi.login(email, password)
    localStorage.setItem('admin_token', data.token)
    localStorage.setItem('admin_user', JSON.stringify(data.user))
    setUser(data.user)
    return data
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch {
      // ignore
    }
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
