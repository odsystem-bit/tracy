import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Bell, AlertTriangle, ShieldAlert, UserPlus, Ban,
  Wallet, BadgeCheck, RefreshCw, CheckCircle2,
} from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import { adminApi } from '../api/admin'
import clsx from 'clsx'

const typeConfig = {
  dispute:    { label: 'Litige',       icon: AlertTriangle, color: 'danger',  bg: 'bg-red-50',    text: 'text-red-600' },
  new_user:   { label: 'Inscription',  icon: UserPlus,      color: 'info',    bg: 'bg-blue-50',   text: 'text-blue-600' },
  banned:     { label: 'Bannissement', icon: Ban,           color: 'warning', bg: 'bg-amber-50',  text: 'text-amber-600' },
  kyc:        { label: 'KYC',          icon: BadgeCheck,    color: 'warning', bg: 'bg-amber-50',  text: 'text-amber-600' },
  withdrawal: { label: 'Retrait',      icon: Wallet,        color: 'warning', bg: 'bg-amber-50',  text: 'text-amber-600' },
  security:   { label: 'Sécurité',     icon: ShieldAlert,   color: 'warning', bg: 'bg-amber-50',  text: 'text-amber-600' },
}

export default function Notifications() {
  const navigate = useNavigate()
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterType, setFilterType] = useState('all')
  const [readIds, setReadIds] = useState(new Set())
  const [lastRefresh, setLastRefresh] = useState(null)

  const fetchNotifications = () => {
    adminApi.getNotifications()
      .then(res => {
        setNotifications(res.data.data || [])
        setLoading(false)
        setLastRefresh(new Date())
      })
      .catch(() => {
        setNotifications([])
        setLoading(false)
        setLastRefresh(new Date())
      })
  }

  useEffect(() => {
    fetchNotifications()
    const interval = setInterval(fetchNotifications, 30000)
    return () => clearInterval(interval)
  }, [])

  const filtered = useMemo(() => {
    if (filterType === 'all') return notifications
    return notifications.filter(n => n.type === filterType)
  }, [notifications, filterType])

  const handleMarkRead = (id) => {
    setReadIds(prev => new Set([...prev, id]))
  }

  const handleMarkAllRead = () => {
    setReadIds(new Set(notifications.map(n => n.id)))
  }

  const handleRefresh = () => {
    setLoading(true)
    fetchNotifications()
  }

  const stats = {
    total: notifications.length,
    disputes: notifications.filter(n => n.type === 'dispute').length,
    newUsers: notifications.filter(n => n.type === 'new_user').length,
    security: notifications.filter(n => n.type === 'security' || n.type === 'banned').length,
  }

  const remainingUnread = notifications.filter(n => !readIds.has(n.id)).length

  return (
    <div className="space-y-6">
      <PageHeader
        title="Notifications"
        description="Alertes temps réel — litiges, sécurité, inscriptions, retraits et KYC"
        icon={Bell}
        badge={remainingUnread > 0 ? (
          <Badge variant="danger">
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse"></span>
            {remainingUnread} non lues
          </Badge>
        ) : (
          <Badge variant="success">
            <CheckCircle2 className="w-3 h-3" />
            À jour
          </Badge>
        )}
        actions={
          <>
            <button onClick={handleRefresh} className="btn-secondary">
              <RefreshCw className={clsx('w-4 h-4', loading && 'animate-spin')} />
              Actualiser
            </button>
            {remainingUnread > 0 && (
              <button onClick={handleMarkAllRead} className="btn-primary">
                <CheckCircle2 className="w-4 h-4" />
                Tout marquer lu
              </button>
            )}
          </>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total alertes" value={stats.total} icon={Bell} color="mantota" />
        <StatCard label="Litiges" value={stats.disputes} icon={AlertTriangle} color="red" />
        <StatCard label="Nouvelles inscriptions" value={stats.newUsers} icon={UserPlus} color="blue" />
        <StatCard label="Alertes sécurité" value={stats.security} icon={ShieldAlert} color="amber" />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <button
          onClick={() => setFilterType('all')}
          className={clsx('px-3 py-2 rounded-lg text-sm font-medium transition-colors',
            filterType === 'all' ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          )}
        >
          Toutes ({notifications.length})
        </button>
        {Object.entries(typeConfig).map(([type, cfg]) => {
          const count = notifications.filter(n => n.type === type).length
          if (count === 0) return null
          return (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={clsx('flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                filterType === type ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              )}
            >
              <cfg.icon className="w-3.5 h-3.5" />
              {cfg.label} ({count})
            </button>
          )
        })}
      </div>

      {/* Last refresh indicator */}
      {lastRefresh && (
        <div className="text-xs text-slate-400 flex items-center gap-1.5">
          <RefreshCw className="w-3 h-3" />
          Dernière actualisation: {lastRefresh.toLocaleTimeString('fr-FR')} · Auto-refresh 30s
        </div>
      )}

      {/* Notifications list */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-10 h-10 border-3 border-mantota-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <CheckCircle2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
            <p className="text-sm text-slate-400">Aucune notification</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-50">
            {filtered.map(n => {
              const cfg = typeConfig[n.type] || { label: n.type, icon: Bell, bg: 'bg-slate-50', text: 'text-slate-600' }
              const isRead = readIds.has(n.id)
              return (
                <div
                  key={n.id}
                  className={clsx('flex items-start gap-4 p-4 hover:bg-slate-50 transition-colors cursor-pointer', !isRead && 'bg-mantota-50/30')}
                  onClick={() => {
                    handleMarkRead(n.id)
                    if (n.link) navigate(n.link)
                  }}
                >
                  <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center shrink-0', cfg.bg)}>
                    <cfg.icon className={clsx('w-5 h-5', cfg.text)} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-slate-900">{n.title}</p>
                      <Badge variant={cfg.color}>{cfg.label}</Badge>
                      {!isRead && <span className="w-2 h-2 bg-mantota-500 rounded-full shrink-0"></span>}
                    </div>
                    <p className="text-sm text-slate-600 mt-0.5">{n.message}</p>
                    <p className="text-xs text-slate-400 mt-1">
                      {n.created_at ? new Date(n.created_at).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' }) : '—'}
                    </p>
                  </div>
                  {!isRead && (
                    <button
                      onClick={(e) => { e.stopPropagation(); handleMarkRead(n.id) }}
                      className="text-xs text-slate-400 hover:text-mantota-600 shrink-0"
                    >
                      Marquer lu
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
