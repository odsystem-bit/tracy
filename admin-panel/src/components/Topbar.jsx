import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Bell, Menu, ChevronDown, AlertTriangle, UserPlus, Ban, Wallet, BadgeCheck, ShieldAlert, CheckCircle2 } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { adminApi } from '../api/admin'
import clsx from 'clsx'

const typeConfig = {
  dispute:    { icon: AlertTriangle, bg: 'bg-red-50',    text: 'text-red-600' },
  new_user:   { icon: UserPlus,      bg: 'bg-blue-50',   text: 'text-blue-600' },
  banned:     { icon: Ban,           bg: 'bg-amber-50',  text: 'text-amber-600' },
  kyc:        { icon: BadgeCheck,    bg: 'bg-amber-50',  text: 'text-amber-600' },
  withdrawal: { icon: Wallet,        bg: 'bg-amber-50',  text: 'text-amber-600' },
  security:   { icon: ShieldAlert,   bg: 'bg-amber-50',  text: 'text-amber-600' },
}

export default function Topbar({ onToggleSidebar }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [notifOpen, setNotifOpen] = useState(false)
  const [notifications, setNotifications] = useState([])
  const [readIds, setReadIds] = useState(new Set())
  const dropdownRef = useRef(null)

  useEffect(() => {
    const fetchNotifs = () => {
      adminApi.getNotifications()
        .then(res => {
          setNotifications(res.data.data || [])
        })
        .catch(() => {})
    }
    fetchNotifs()
    const interval = setInterval(fetchNotifs, 30000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setNotifOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const remainingUnread = notifications.filter(n => !readIds.has(n.id)).length
  const topNotifs = notifications.slice(0, 8)

  const handleNotifClick = (n) => {
    setReadIds(prev => new Set([...prev, n.id]))
    setNotifOpen(false)
    if (n.link) navigate(n.link)
  }

  const handleMarkAllRead = () => {
    setReadIds(new Set(notifications.map(n => n.id)))
  }

  return (
    <header className="h-16 bg-white border-b border-slate-100 flex items-center justify-between px-6 sticky top-0 z-30">
      <div className="flex items-center gap-4 flex-1">
        <button
          onClick={onToggleSidebar}
          className="btn-ghost p-2 rounded-lg lg:hidden"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div className="relative max-w-md flex-1 hidden md:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Rechercher utilisateur, commande, boutique..."
            className="input pl-9 py-2 bg-slate-50 border-transparent focus:bg-white"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setNotifOpen(!notifOpen)}
            className="btn-ghost p-2 rounded-lg relative"
          >
            <Bell className="w-5 h-5" />
            {remainingUnread > 0 && (
              <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 bg-coral-500 rounded-full ring-2 ring-white flex items-center justify-center">
                <span className="text-[10px] font-bold text-white leading-none">{remainingUnread > 9 ? '9+' : remainingUnread}</span>
              </span>
            )}
          </button>
          {notifOpen && (
            <div className="absolute right-0 mt-2 w-96 card p-0 animate-fade-in z-50 max-h-[70vh] flex flex-col">
              <div className="flex items-center justify-between p-4 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <p className="font-semibold text-sm">Notifications</p>
                  {remainingUnread > 0 && (
                    <span className="text-xs bg-coral-100 text-coral-700 px-2 py-0.5 rounded-full font-medium">{remainingUnread} non lues</span>
                  )}
                </div>
                {remainingUnread > 0 && (
                  <button onClick={handleMarkAllRead} className="text-xs text-mantota-600 hover:text-mantota-700 font-medium">
                    Tout marquer lu
                  </button>
                )}
              </div>
              <div className="overflow-y-auto flex-1">
                {topNotifs.length === 0 ? (
                  <div className="text-center py-8">
                    <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="text-sm text-slate-400">Aucune notification</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-50">
                    {topNotifs.map(n => {
                      const cfg = typeConfig[n.type] || { icon: Bell, bg: 'bg-slate-50', text: 'text-slate-600' }
                      const isRead = readIds.has(n.id)
                      return (
                        <div
                          key={n.id}
                          onClick={() => handleNotifClick(n)}
                          className={clsx('flex items-start gap-3 p-3 hover:bg-slate-50 transition-colors cursor-pointer', !isRead && 'bg-mantota-50/30')}
                        >
                          <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center shrink-0', cfg.bg)}>
                            <cfg.icon className={clsx('w-4 h-4', cfg.text)} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-slate-900 truncate">{n.title}</p>
                            <p className="text-xs text-slate-500 truncate">{n.message}</p>
                            <p className="text-[10px] text-slate-400 mt-0.5">
                              {n.created_at ? new Date(n.created_at).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : ''}
                            </p>
                          </div>
                          {!isRead && <span className="w-2 h-2 bg-mantota-500 rounded-full shrink-0 mt-1.5"></span>}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
              {notifications.length > 0 && (
                <div className="p-3 border-t border-slate-100 text-center">
                  <button
                    onClick={() => { setNotifOpen(false); navigate('/push-notifs') }}
                    className="text-xs text-mantota-600 hover:text-mantota-700 font-medium"
                  >
                    Voir toutes les notifications →
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="h-6 w-px bg-slate-200"></div>

        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center overflow-hidden">
            <img src="/mantota-logo.png" alt="Admin" className="h-6 w-auto" />
          </div>
          <div className="hidden md:block">
            <p className="text-sm font-semibold text-slate-700">{user?.name || 'Admin'}</p>
            <p className="text-xs text-slate-400">{user?.email || 'admin@mantota.com'}</p>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400 hidden md:block" />
        </div>
      </div>
    </header>
  )
}
