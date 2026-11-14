import { useState, useEffect } from 'react'
import {
  Activity, Zap, ShoppingBag, Users, DollarSign, AlertTriangle,
  Clock, TrendingUp, Bot, ShieldCheck, Package, Store,
  CheckCircle2, ArrowRight,
} from 'lucide-react'
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'
import { adminApi } from '../api/admin'

const typeIcons = {
  user_registered: Users,
  order_created: ShoppingBag,
  transaction: DollarSign,
}

export default function Operations() {
  const [feed, setFeed] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')

  useEffect(() => {
    const fetchFeed = async () => {
      try {
        const { data } = await adminApi.getLiveFeed()
        setFeed(data.data || [])
      } catch {
        // silent
      }
      setLoading(false)
    }
    fetchFeed()
    const interval = setInterval(fetchFeed, 15000)
    return () => clearInterval(interval)
  }, [])

  const filtered = filter === 'all' ? feed : feed.filter(f => f.type === filter)

  const filters = [
    { id: 'all', label: 'Tout', count: feed.length },
    { id: 'user_registered', label: 'Users', count: feed.filter(f => f.type === 'user_registered').length },
    { id: 'order_created', label: 'Commandes', count: feed.filter(f => f.type === 'order_created').length },
    { id: 'transaction', label: 'Transactions', count: feed.filter(f => f.type === 'transaction').length },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Centre d'opérations"
        description="Flux d'activité temps réel et interventions rapides sur la plateforme"
        icon={Activity}
        badge={
          <Badge variant="success">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
            Live
          </Badge>
        }
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="Activité (live)" value={feed.length} icon={Activity} color="mantota" />
        <StatCard label="Users récents" value={feed.filter(f => f.type === 'user_registered').length} icon={Users} color="blue" />
        <StatCard label="Commandes récentes" value={feed.filter(f => f.type === 'order_created').length} icon={ShoppingBag} color="coral" />
        <StatCard label="Transactions" value={feed.filter(f => f.type === 'transaction').length} icon={DollarSign} color="purple" />
        <StatCard label="Alertes actives" value="0" icon={AlertTriangle} color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live feed — 2/3 */}
        <div className="lg:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900 flex items-center gap-2">
              <Zap className="w-4 h-4 text-mantota-500" />
              Flux temps réel
            </h3>
            <div className="flex items-center gap-1">
              {filters.map(f => (
                <button
                  key={f.id}
                  onClick={() => setFilter(f.id)}
                  className={clsx('px-2.5 py-1 rounded-md text-xs font-medium transition-colors',
                    filter === f.id ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  )}
                >
                  {f.label} <span className="opacity-60">({f.count})</span>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2 max-h-[520px] overflow-y-auto sidebar-scroll">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-8 text-sm text-slate-400">Aucune activité récente</div>
            ) : filtered.map((item, i) => {
              const Icon = typeIcons[item.type] || Activity
              return (
                <div key={i} className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors animate-slide-in">
                  <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 bg-blue-50 text-blue-500">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-900">{item.message}</p>
                    <p className="text-xs text-slate-400">{item.type}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-[10px] text-slate-400">{item.time ? new Date(item.time).toLocaleTimeString() : ''}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Right column — live activity + quick actions */}
        <div className="space-y-6">
          <div className="card p-5">
            <h3 className="font-semibold text-slate-900 mb-3">Activité live (15min)</h3>
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={[
                { time: '00h', value: 0 }, { time: '04h', value: 0 },
                { time: '08h', value: 0 }, { time: '12h', value: 0 },
                { time: '16h', value: 0 }, { time: '20h', value: 0 },
              ]}>
                <defs>
                  <linearGradient id="colorLive" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0BBFA0" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#0BBFA0" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis hide />
                <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
                <Area type="monotone" dataKey="value" stroke="#0BBFA0" strokeWidth={2} fill="url(#colorLive)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="card p-5">
            <h3 className="font-semibold text-slate-900 mb-3">Actions rapides</h3>
            <div className="space-y-2">
              <QuickAction icon={ShieldCheck} label="Valider KYC en attente" count={0} color="text-amber-600 bg-amber-50" />
              <QuickAction icon={DollarSign} label="Approuver retraits" count={0} color="text-coral-600 bg-coral-500/10" />
              <QuickAction icon={AlertTriangle} label="Litiges non résolus" count={0} color="text-red-600 bg-red-50" />
              <QuickAction icon={Bot} label="Conversations en fallback" count={0} color="text-purple-600 bg-purple-50" />
            </div>
          </div>

          <div className="card p-5">
            <h3 className="font-semibold text-slate-900 mb-3">Santé système</h3>
            <div className="space-y-3">
              <HealthRow label="API Laravel" status="ok" value="—" />
              <HealthRow label="Tracy Core" status="ok" value="—" />
              <HealthRow label="PostgreSQL" status="ok" value="—" />
              <HealthRow label="Redis Queue" status="ok" value="—" />
              <HealthRow label="Reverb WS" status="ok" value="—" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function QuickAction({ icon: Icon, label, count, color }) {
  return (
    <button className="w-full flex items-center gap-3 p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors group">
      <div className={clsx('w-9 h-9 rounded-lg flex items-center justify-center shrink-0', color)}>
        <Icon className="w-4 h-4" />
      </div>
      <span className="text-sm font-medium text-slate-700 flex-1 text-left">{label}</span>
      <span className="badge bg-slate-100 text-slate-600 group-hover:bg-mantota-100 group-hover:text-mantota-700 transition-colors">{count}</span>
    </button>
  )
}

function HealthRow({ label, status, value }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <span className={clsx('w-2 h-2 rounded-full', status === 'ok' ? 'bg-green-500' : 'bg-red-500')}></span>
        <span className="text-sm text-slate-600">{label}</span>
      </div>
      <span className="text-xs font-medium text-slate-400">{value}</span>
    </div>
  )
}
