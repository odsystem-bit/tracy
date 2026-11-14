import { useState, useEffect } from 'react'
import {
  DollarSign, TrendingUp, Percent, Calculator, Download,
  ArrowUpRight, ArrowDownRight, CreditCard, Wallet, Store,
  Sparkles, ShoppingBag,
} from 'lucide-react'
import {
  AreaChart, Area, PieChart, Pie, Cell, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'
import { adminApi } from '../api/admin'

const COLORS = ['#0BBFA0', '#3B82F6', '#FF6B35', '#8B5CF6', '#F59E0B']

const planPricing = {
  free: { price: 0, convLimit: 50, features: ['1 boutique', '50 conv/mois', 'Tracy hybride 60s'] },
  starter: { price: 3000, convLimit: 999, features: ['1 boutique', 'Conv illimitées', 'Tracy hybride 60s', 'Analytics base'] },
  standard: { price: 15000, convLimit: 999, features: ['2 boutiques', 'Conv illimitées', 'Tracy hybride 30s', 'Analytics avancées', 'Support prioritaire'] },
  pro: { price: 60000, convLimit: 999, features: ['Boutiques illimitées', 'Conv illimitées', 'Tracy hybride 15s', 'API access', 'Manager dédié'] },
}

export default function Revenue() {
  const [commissionRate, setCommissionRate] = useState(5)
  const [withdrawalFee, setWithdrawalFee] = useState(5)
  const [simulatedVolume, setSimulatedVolume] = useState(10000000)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminApi.getRevenue()
      .then(({ data }) => setData(data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const s = data?.summary || {}
  const series = data?.series || []
  const planBreakdown = data?.plan_breakdown || []

  const commissionRevenue = Math.round(simulatedVolume * commissionRate / 100)
  const withdrawalRevenue = Math.round(simulatedVolume * 0.3 * withdrawalFee / 100)
  const subscriptionRevenue = s.total_commission || 0
  const totalProjected = commissionRevenue + withdrawalRevenue + subscriptionRevenue

  const planDistribution = planBreakdown.map((p, i) => ({
    name: p.bot_plan || 'free',
    users: p.vendors,
    revenue: 0,
    color: COLORS[i % COLORS.length],
  }))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Revenus & Commissions"
        description="Breakdown par source, simulateur de frais et projections"
        icon={DollarSign}
        actions={
          <button className="btn-secondary">
            <Download className="w-4 h-4" />
            Export
          </button>
        }
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Revenu net" value={`${Math.round((s.net_revenue || 0)).toLocaleString()} FCFA`} icon={DollarSign} color="mantota" />
        <StatCard label="Commissions" value={`${Math.round((s.total_commission || 0)).toLocaleString()} FCFA`} icon={Percent} color="coral" />
        <StatCard label="Dépôts" value={`${Math.round((s.total_deposits || 0)).toLocaleString()} FCFA`} icon={CreditCard} color="blue" />
        <StatCard label="Frais de retrait" value={`${Math.round((s.total_withdrawals || 0)).toLocaleString()} FCFA`} icon={Wallet} color="purple" />
      </div>

      {/* Revenue evolution */}
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-1">Évolution commissions & volume (30 jours)</h3>
        <p className="text-xs text-slate-400 mb-4">Revenus quotidiens sur commandes livrées</p>
        {loading ? (
          <div className="flex items-center justify-center h-[300px]"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
        ) : (
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={series}>
            <defs>
              <linearGradient id="colorComm" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} /><stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorGross" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0BBFA0" stopOpacity={0.3} /><stop offset="95%" stopColor="#0BBFA0" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v / 1000}k`} />
            <Tooltip formatter={(value) => `${Number(value).toLocaleString()} FCFA`} contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
            <Legend wrapperStyle={{ fontSize: '12px' }} />
            <Area type="monotone" dataKey="gross" name="Volume brut" stroke="#0BBFA0" strokeWidth={2.5} fill="url(#colorGross)" />
            <Area type="monotone" dataKey="commission" name="Commissions" stroke="#3B82F6" strokeWidth={2.5} fill="url(#colorComm)" />
          </AreaChart>
        </ResponsiveContainer>
        )}
      </div>

      {/* Plan distribution + Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="font-semibold text-slate-900 mb-4">Distribution des plans vendeurs</h3>
          {planDistribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={planDistribution} dataKey="users" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3}>
                  {planDistribution.map((entry, i) => (
                    <Cell key={i} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[200px] flex items-center justify-center text-sm text-slate-400">Aucune donnée</div>
          )}
          <div className="space-y-2 mt-2">
            {planDistribution.map(p => (
              <div key={p.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ background: p.color }}></span>
                  <span className="text-slate-600 capitalize">{p.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-slate-400">{p.users} vendeurs</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Simulator */}
        <div className="card p-6">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2 mb-4">
            <Calculator className="w-4 h-4 text-mantota-500" />
            Simulateur de revenus
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-slate-700">Taux de commission</label>
                <span className="text-sm font-bold text-mantota-600">{commissionRate}%</span>
              </div>
              <input type="range" min={1} max={15} step={0.5} value={commissionRate}
                onChange={e => setCommissionRate(Number(e.target.value))}
                className="w-full h-2 rounded-full appearance-none bg-slate-200 accent-mantota-500 cursor-pointer" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-slate-700">Frais de retrait</label>
                <span className="text-sm font-bold text-mantota-600">{withdrawalFee}%</span>
              </div>
              <input type="range" min={1} max={20} step={0.5} value={withdrawalFee}
                onChange={e => setWithdrawalFee(Number(e.target.value))}
                className="w-full h-2 rounded-full appearance-none bg-slate-200 accent-mantota-500 cursor-pointer" />
            </div>
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-slate-700">Volume mensuel simulé</label>
                <span className="text-sm font-bold text-mantota-600">{simulatedVolume.toLocaleString()} FCFA</span>
              </div>
              <input type="range" min={1000000} max={50000000} step={500000} value={simulatedVolume}
                onChange={e => setSimulatedVolume(Number(e.target.value))}
                className="w-full h-2 rounded-full appearance-none bg-slate-200 accent-mantota-500 cursor-pointer" />
            </div>

            <div className="pt-4 border-t border-slate-100 space-y-2">
              <SimRow label="Revenus commissions" value={commissionRevenue} icon={Percent} color="text-blue-600" />
              <SimRow label="Revenus retraits" value={withdrawalRevenue} icon={Wallet} color="text-coral-600" />
              <SimRow label="Revenus abonnements" value={subscriptionRevenue} icon={CreditCard} color="text-mantota-600" />
              <div className="flex items-center justify-between p-3 rounded-lg bg-mantota-50 border border-mantota-100">
                <span className="font-semibold text-mantota-700">Total projeté / mois</span>
                <span className="text-xl font-bold text-mantota-700">{totalProjected.toLocaleString()} FCFA</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Plan pricing cards */}
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Configuration des plans vendeurs</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(planPricing).map(([name, plan]) => (
            <div key={name} className={clsx('p-5 rounded-xl border-2 transition-colors',
              name === 'pro' ? 'border-purple-200 bg-purple-50/30' :
              name === 'standard' ? 'border-blue-200 bg-blue-50/30' :
              name === 'starter' ? 'border-mantota-200 bg-mantota-50/30' :
              'border-slate-200 bg-slate-50/30'
            )}>
              <div className="flex items-center justify-between mb-3">
                <span className={clsx('font-bold capitalize text-lg',
                  name === 'pro' ? 'text-purple-600' : name === 'standard' ? 'text-blue-600' :
                  name === 'starter' ? 'text-mantota-600' : 'text-slate-600'
                )}>{name}</span>
                {name !== 'free' && <Badge variant="info">{plan.convLimit === 999 ? 'Illimité' : `${plan.convLimit} conv`}</Badge>}
              </div>
              <p className="text-2xl font-bold text-slate-900 mb-1">
                {plan.price.toLocaleString()} <span className="text-sm font-normal text-slate-400">FCFA/mois</span>
              </p>
              <div className="space-y-1.5 mt-3">
                {plan.features.map((f, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-slate-600">
                    <span className="w-1.5 h-1.5 rounded-full bg-mantota-500 shrink-0"></span>
                    {f}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function SimRow({ label, value, icon: Icon, color }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <Icon className={clsx('w-3.5 h-3.5', color)} />
        <span className="text-sm text-slate-600">{label}</span>
      </div>
      <span className="text-sm font-semibold text-slate-900">{value.toLocaleString()} FCFA</span>
    </div>
  )
}
