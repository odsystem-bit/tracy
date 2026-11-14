import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { Shield, Mail, Lock, Eye, EyeOff, AlertCircle, Loader2 } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('admin@mantota.test')
  const [password, setPassword] = useState('admin123')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.message || 'Identifiants incorrects')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-sidebar relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-mantota-900/20 via-sidebar to-sidebar"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-mantota-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-coral-500/5 rounded-full blur-3xl translate-y-1/2 -translate-x-1/2"></div>

        <div className="relative z-10 flex flex-col justify-between p-12 text-white w-full">
          <div className="flex items-center gap-3">
            <img src="/mantota-logo.png" alt="MANTOTA" className="h-11 w-auto" />
            <div>
              <p className="font-bold text-lg">MANTOTA</p>
              <p className="text-slate-400 text-xs">Commerce conversationnel</p>
            </div>
          </div>

          <div className="max-w-md">
            <h1 className="text-4xl font-bold leading-tight mb-4">
              Panel<br />
              <span className="text-mantota-400">Administration</span>
            </h1>
            <p className="text-slate-400 text-lg leading-relaxed">
              Pilotez votre plateforme en temps réel. Boutiques, utilisateurs, finances, IA Tracy — tout au même endroit.
            </p>
            <div className="flex items-center gap-6 mt-8">
              <div>
                <p className="text-3xl font-bold text-mantota-400">35</p>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Pages</p>
              </div>
              <div className="h-10 w-px bg-slate-700"></div>
              <div>
                <p className="text-3xl font-bold text-mantota-400">11</p>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Modules</p>
              </div>
              <div className="h-10 w-px bg-slate-700"></div>
              <div>
                <p className="text-3xl font-bold text-mantota-400">24/7</p>
                <p className="text-xs text-slate-500 uppercase tracking-wider">Live</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 text-slate-500 text-xs">
            <Shield className="w-4 h-4" />
            <span>Connexion sécurisée · IP allowlist · Audit log</span>
          </div>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12 bg-slate-50">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 mb-8 lg:hidden">
            <img src="/mantota-logo.png" alt="MANTOTA" className="h-10 w-auto" />
            <div>
              <p className="font-bold text-slate-900">MANTOTA</p>
              <p className="text-slate-400 text-xs">Admin Panel</p>
            </div>
          </div>

          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900">Connexion</h2>
            <p className="text-slate-500 text-sm mt-1">Accès réservé aux administrateurs</p>
          </div>

          {error && (
            <div className="flex items-center gap-2.5 px-4 py-3 rounded-lg bg-red-50 border border-red-100 mb-5 animate-fade-in">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Email</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" style={{ width: 18, height: 18 }} />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="admin@mantota.com"
                  className="input pl-10"
                  autoFocus
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">Mot de passe</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4.5 h-4.5 text-slate-400" style={{ width: 18, height: 18 }} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="input pl-10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4.5 h-4.5" style={{ width: 18, height: 18 }} /> : <Eye className="w-4.5 h-4.5" style={{ width: 18, height: 18 }} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full py-3 text-base"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Connexion...
                </>
              ) : (
                'Se connecter'
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100">
            <p className="text-xs text-slate-400 text-center">
              IP non reconnue ?{' '}
              <a href="/ip-recovery" className="text-mantota-600 hover:text-mantota-700 font-medium">
                Récupérer mon accès
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
