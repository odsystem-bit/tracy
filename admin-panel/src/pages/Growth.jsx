import { useState, useEffect } from 'react'
import {
  TrendingUp, Users, UserPlus, UserMinus, Repeat, DollarSign,
  Target, Zap, Clock, ArrowUpRight, ArrowDownRight, Calendar,
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'
import { adminApi } from '../api/admin'

export default function Growth() {
  const [activeTab, setActiveTab] = useState('overview')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminApi.getGrowth()
      .then(({ data }) => setData(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const s = data?.summary || {}
  const series = data?.series || []

  const tabs = [
    { id: 'overview', label: 'Vue d\'ensemble', icon: TrendingUp },
    { id: 'funnel', label: 'Funnel onboarding', icon: Target },
    { id: 'cohorts', label: 'Cohortes', icon: Users },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Croissance & Rétention"
        description="Funnel d'onboarding, analyse par cohortes, churn et MRR"
        icon={TrendingUp}
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total users" value={s.total_users || 0} icon={Users} color="mantota" />
        <StatCard label="Nouveaux (30j)" value={s.new_users_30d || 0} icon={UserPlus} color="blue" />
        <StatCard label="Total commandes" value={s.total_orders || 0} icon={Target} color="coral" />
        <StatCard label="Commandes (30j)" value={s.new_orders_30d || 0} icon={DollarSign} color="purple" />
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === tab.id ? 'text-mantota-600 border-mantota-500' : 'text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-50'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      <div className="animate-fade-in">
        {activeTab === 'overview' && <OverviewTab series={series} loading={loading} />}
        {activeTab === 'funnel' && <div className="card p-12 text-center text-slate-400">Funnel onboarding — données disponibles une fois l\'app Flutter en production</div>}
        {activeTab === 'cohorts' && <div className="card p-12 text-center text-slate-400">Analyse par cohortes — données disponibles une fois l\'app Flutter en production</div>}
      </div>
    </div>
  )
}

function OverviewTab({ series, loading }) {
  if (loading) {
    return <div className="card p-12 flex items-center justify-center"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
  }
  if (!series.length) {
    return <div className="card p-12 text-center text-slate-400">Aucune donnée disponible</div>
  }
  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-1">Croissance utilisateurs & commandes (30 jours)</h3>
        <p className="text-xs text-slate-400 mb-4">Nouveaux users et commandes par jour</p>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={series}>
            <defs>
              <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0BBFA0" stopOpacity={0.3} /><stop offset="95%" stopColor="#0BBFA0" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorOrders" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} /><stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Area type="monotone" dataKey="users" name="Nouveaux users" stroke="#0BBFA0" strokeWidth={2.5} fill="url(#colorUsers)" />
            <Area type="monotone" dataKey="orders" name="Commandes" stroke="#3B82F6" strokeWidth={2.5} fill="url(#colorOrders)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-1">Revenus quotidiens (30 jours)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={series}>
            <defs>
              <linearGradient id="colorRev" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} /><stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v / 1000}k`} />
            <Tooltip formatter={(value) => `${Number(value).toLocaleString()} FCFA`} contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
            <Area type="monotone" dataKey="revenue" name="Revenu" stroke="#8B5CF6" strokeWidth={2.5} fill="url(#colorRev)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
