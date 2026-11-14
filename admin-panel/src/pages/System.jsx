import { useState, useEffect } from 'react'
import {
  Settings, Cog, Percent, DollarSign, Globe2, Database,
  Server, HardDrive, Activity, Download, Upload, RefreshCw,
  CheckCircle2, AlertCircle, Clock, FileText, Search,
  ShieldCheck, Cpu, MemoryStick,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'
import { adminApi } from '../api/admin'

export default function System() {
  const [activeTab, setActiveTab] = useState('settings')
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminApi.getSystemHealth()
      .then(({ data }) => setHealth(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const tabs = [
    { id: 'settings', label: 'Réglages globaux', icon: Settings },
    { id: 'audit', label: 'Audit log', icon: FileText },
    { id: 'health', label: 'Santé système', icon: Activity },
    { id: 'backup', label: 'Sauvegarde', icon: Database },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Système"
        description="Configuration plateforme, audit, santé système et sauvegardes"
        icon={Cog}
      />

      <div className="flex items-center gap-1 border-b border-slate-200 overflow-x-auto">
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={clsx('flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
              activeTab === tab.id ? 'text-mantota-600 border-mantota-500' : 'text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-50'
            )}>
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="animate-fade-in">
        {activeTab === 'settings' && <SettingsTab />}
        {activeTab === 'audit' && <AuditTab />}
        {activeTab === 'health' && <HealthTab health={health} loading={loading} />}
        {activeTab === 'backup' && <BackupTab />}
      </div>
    </div>
  )
}

function SettingsTab() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Modèle économique</h3>
        <div className="space-y-4">
          <ConfigRow label="Commission par transaction" value="5%" />
          <ConfigRow label="Frais de retrait" value="5%" />
          <ConfigRow label="Markup passerelle paiement" value="2%" />
          <ConfigRow label="Escrow (délai auto-libération)" value="48h" />
          <ConfigRow label="Frais livraison (défaut)" value="500 FCFA" />
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Plans vendeurs</h3>
        <div className="space-y-3">
          <PlanRow name="Free" price="0 FCFA" convs="50/mois" />
          <PlanRow name="Starter" price="3 000 FCFA" convs="Illimité" />
          <PlanRow name="Standard" price="15 000 FCFA" convs="Illimité" />
          <PlanRow name="Pro" price="60 000 FCFA" convs="Illimité" />
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Passerelles de paiement</h3>
        <div className="space-y-3">
          <GatewayRow name="FedaPay" status="active" countries="BJ, CI, SN, TG" />
          <GatewayRow name="Moneroo" status="active" countries="BJ, CI, GH, NG" />
          <GatewayRow name="Mobile Money Direct" status="inactive" countries="—" />
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Sécurité & accès</h3>
        <div className="space-y-3">
          <ToggleRow label="2FA obligatoire pour admins" enabled={true} />
          <ToggleRow label="IP allowlist admin" enabled={true} />
          <ToggleRow label="Audit log toutes actions" enabled={true} />
          <ToggleRow label="Mode maintenance" enabled={false} />
          <ToggleRow label="Inscriptions ouvertes" enabled={true} />
        </div>
      </div>
    </div>
  )
}

function AuditTab() {
  return (
    <div className="card p-12 text-center text-slate-400">
      <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
      <p className="font-medium">Audit log</p>
      <p className="text-sm mt-1">Les logs d'audit seront disponibles une fois le système d'audit implémenté côté API.</p>
    </div>
  )
}

function HealthTab({ health, loading }) {
  if (loading) {
    return <div className="flex items-center justify-center py-12"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
  }
  const services = health?.services || []
  const resources = health?.resources || {}
  const series = health?.series || []
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {services.length > 0 ? services.map((svc, i) => {
          const icons = [Server, Cpu, Database, Activity]
          const Icon = icons[i % icons.length]
          return (
            <div key={i} className="card p-5">
              <div className="flex items-center justify-between mb-3">
                <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center',
                  svc.status === 'ok' ? 'bg-green-50' : 'bg-red-50'
                )}>
                  <Icon className={clsx('w-5 h-5', svc.status === 'ok' ? 'text-green-600' : 'text-red-500')} />
                </div>
                <Badge variant={svc.status === 'ok' ? 'success' : 'danger'}>{svc.status === 'ok' ? 'OK' : 'DOWN'}</Badge>
              </div>
              <p className="stat-label">{svc.name}</p>
              <p className="stat-value mt-1">{svc.latency || svc.detail || '—'}</p>
            </div>
          )
        }) : (
          <div className="col-span-4 card p-12 text-center text-slate-400">Aucune donnée système disponible</div>
        )}
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Utilisation des ressources (30min)</h3>
        {series.length > 0 ? (
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={series}>
            <defs>
              <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0BBFA0" stopOpacity={0.3} /><stop offset="95%" stopColor="#0BBFA0" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorRam" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} /><stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="time" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v}%`} />
            <Tooltip formatter={(value) => `${value}%`} contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
            <Area type="monotone" dataKey="cpu" name="CPU" stroke="#0BBFA0" strokeWidth={2.5} fill="url(#colorCpu)" />
            <Area type="monotone" dataKey="ram" name="RAM" stroke="#3B82F6" strokeWidth={2.5} fill="url(#colorRam)" />
          </AreaChart>
        </ResponsiveContainer>
        ) : (
          <div className="h-[280px] flex items-center justify-center text-sm text-slate-400">Données système non disponibles — nécessite un serveur de monitoring</div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <ResourceCard icon={Cpu} label="CPU" value={`${resources.cpu || '—'}%`} detail={resources.cpu_detail || 'N/A'} />
        <ResourceCard icon={MemoryStick} label="RAM" value={`${resources.ram || '—'}%`} detail={resources.ram_detail || 'N/A'} />
        <ResourceCard icon={HardDrive} label="Disque" value={`${resources.disk || '—'}%`} detail={resources.disk_detail || 'N/A'} />
      </div>
    </div>
  )
}

function BackupTab() {
  return (
    <div className="card p-12 text-center text-slate-400">
      <Database className="w-12 h-12 mx-auto mb-3 text-slate-300" />
      <p className="font-medium">Sauvegardes</p>
      <p className="text-sm mt-1">La gestion des sauvegardes sera configurée lors du déploiement sur VPS.</p>
    </div>
  )
}

function ConfigRow({ label, value }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg border border-slate-100">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-bold text-mantota-600">{value}</span>
        <button className="text-xs text-slate-400 hover:text-mantota-600 font-medium">Modifier</button>
      </div>
    </div>
  )
}

function PlanRow({ name, price, convs }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg border border-slate-100">
      <span className="text-sm font-medium text-slate-700">{name}</span>
      <div className="flex items-center gap-3">
        <span className="text-sm font-bold text-slate-900">{price}</span>
        <span className="text-xs text-slate-400">{convs}</span>
      </div>
    </div>
  )
}

function GatewayRow({ name, status, countries }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg border border-slate-100">
      <div>
        <p className="text-sm font-medium text-slate-700">{name}</p>
        <p className="text-xs text-slate-400">{countries}</p>
      </div>
      <Badge variant={status === 'active' ? 'success' : 'neutral'}>{status === 'active' ? 'Actif' : 'Inactif'}</Badge>
    </div>
  )
}

function ToggleRow({ label, enabled }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg border border-slate-100">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <button className={clsx('relative w-11 h-6 rounded-full transition-colors', enabled ? 'bg-mantota-500' : 'bg-slate-200')}>
        <span className={clsx('absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform', enabled ? 'translate-x-5' : 'translate-x-0.5')} />
      </button>
    </div>
  )
}

function ResourceCard({ icon: Icon, label, value, detail }) {
  return (
    <div className="card p-5">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
          <Icon className="w-5 h-5 text-slate-500" />
        </div>
        <span className="text-sm font-medium text-slate-700">{label}</span>
      </div>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
      <p className="text-xs text-slate-400 mt-1">{detail}</p>
    </div>
  )
}
