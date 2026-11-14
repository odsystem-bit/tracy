import { useState, useEffect } from 'react'
import {
  Shield, ShieldAlert, Lock, Unlock, MapPin, Monitor,
  Search, Download, Ban, Eye, AlertTriangle, CheckCircle2,
  Clock, Smartphone, Globe2, Activity,
} from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'
import { adminApi } from '../api/admin'

export default function Security() {
  const [activeTab, setActiveTab] = useState('intrusions')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminApi.getSecurity()
      .then(({ data }) => setData(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const intrusions = data?.intrusions || []
  const blockedIps = data?.blocked_ips || []
  const devices = data?.devices || []
  const summary = data?.summary || {}

  const tabs = [
    { id: 'intrusions', label: 'Intrusions', icon: ShieldAlert, count: intrusions.length },
    { id: 'blocked', label: 'IPs bloquées', icon: Ban, count: blockedIps.length },
    { id: 'devices', label: 'Appareils connectés', icon: Monitor, count: devices.length },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sécurité plateforme"
        description="Intrusions détectées, IPs bloquées et appareils connectés"
        icon={Shield}
        badge={<Badge variant="danger"><AlertTriangle className="w-3 h-3" />2 alertes</Badge>}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Tentatives bloquées (24h)" value={summary.blocked_24h || 0} icon={ShieldAlert} color="red" />
        <StatCard label="IPs bloquées" value={blockedIps.length} icon={Ban} color="coral" />
        <StatCard label="Appareils actifs" value={devices.length} icon={Monitor} color="blue" />
        <StatCard label="Score sécurité" value={`${summary.security_score || 0}/100`} icon={Shield} color="mantota" />
      </div>

      <div className="flex items-center gap-1 border-b border-slate-200">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={clsx('flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === tab.id ? 'text-mantota-600 border-mantota-500' : 'text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-50'
            )}>
            <tab.icon className="w-4 h-4" />
            {tab.label}
            <span className="badge bg-slate-100 text-slate-600 text-[10px]">{tab.count}</span>
          </button>
        ))}
      </div>

      <div className="animate-fade-in">
        {loading ? (
          <div className="flex items-center justify-center py-12"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
        ) : (
        <>
        {activeTab === 'intrusions' && (
          <div className="space-y-3">
            {intrusions.length === 0 ? (
              <div className="card p-12 text-center text-slate-400">Aucune intrusion détectée</div>
            ) : intrusions.map((intr, i) => (
              <div key={intr.id} className="card p-5">
                <div className="flex items-start gap-4">
                  <div className={clsx('w-11 h-11 rounded-xl flex items-center justify-center shrink-0',
                    intr.blocked ? 'bg-red-50 text-red-500' : 'bg-amber-50 text-amber-500'
                  )}>
                    <ShieldAlert className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2.5 mb-1">
                      <p className="font-semibold text-slate-900 font-mono text-sm">{intr.ip}</p>
                      <Badge variant={intr.blocked ? 'danger' : 'warning'}>
                        {intr.blocked ? 'Bloquée' : 'Surveillance'}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-600">{intr.reason}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                      <span className="flex items-center gap-1"><Globe2 className="w-3 h-3" />{intr.country}</span>
                      <span className="flex items-center gap-1"><Activity className="w-3 h-3" />{intr.attempts} tentatives</span>
                      <span>Cible: <span className="font-medium text-slate-600">{intr.target}</span></span>
                      <span>{intr.lastAttempt}</span>
                    </div>
                  </div>
                  {!intr.blocked && (
                    <button className="btn-danger text-xs">
                      <Ban className="w-3.5 h-3.5" />
                      Bloquer IP
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'blocked' && (
          <div className="card overflow-hidden">
            {blockedIps.length === 0 ? (
              <div className="p-12 text-center text-slate-400">Aucune IP bloquée</div>
            ) : (
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-100">
                <tr>
                  <th className="table-header">Adresse IP</th>
                  <th className="table-header">Raison</th>
                  <th className="table-header">Tentatives</th>
                  <th className="table-header">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {blockedIps.map((ip, i) => (
                  <tr key={ip.ip} className="table-row">
                    <td className="table-cell font-mono text-sm font-medium text-slate-700">{ip.ip}</td>
                    <td className="table-cell"><Badge variant="danger">{ip.reason}</Badge></td>
                    <td className="table-cell text-sm font-semibold text-red-500">{ip.attempts}</td>
                    <td className="table-cell">
                      <button className="btn-ghost text-xs text-mantota-600 hover:bg-mantota-50">
                        <Unlock className="w-3.5 h-3.5" />
                        Débloquer
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            )}
          </div>
        )}

        {activeTab === 'devices' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {devices.length === 0 ? (
              <div className="card p-12 text-center text-slate-400 col-span-2">Aucun appareil connecté</div>
            ) : devices.map((d, i) => (
              <div key={i} className="card p-5">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center shrink-0">
                    <Smartphone className="w-5 h-5 text-slate-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-slate-900 text-sm truncate">{d.user}</p>
                      {d.trusted ? <Badge variant="success"><CheckCircle2 className="w-3 h-3" />Approuvé</Badge> : <Badge variant="warning">Non approuvé</Badge>}
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">{d.device}</p>
                    <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                      <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{d.location}</span>
                      <span className="font-mono">{d.ip}</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-1 flex items-center gap-1"><Clock className="w-3 h-3" />{d.lastSeen}</p>
                  </div>
                  <button className="btn-ghost p-1.5 rounded-lg text-red-500 hover:bg-red-50">
                    <Ban className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
        </>
        )}
      </div>
    </div>
  )
}
