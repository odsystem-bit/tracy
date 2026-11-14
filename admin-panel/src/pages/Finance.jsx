import { useState, useEffect } from 'react'
import {
  DollarSign, TrendingUp, TrendingDown, Wallet, ArrowUpRight, ArrowDownRight,
  Download, Check, X, AlertTriangle, Search, ChevronDown, Eye,
  Banknote, Shield, Clock,
} from 'lucide-react'
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import { adminApi } from '../api/admin'
import clsx from 'clsx'

const COLORS = ['#0BBFA0', '#FF6B35', '#3B82F6', '#F59E0B', '#8B5CF6']

export default function Finance() {
  const [activeTab, setActiveTab] = useState('cashflow')
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('pending')
  const [financeData, setFinanceData] = useState(null)
  const [revenueData, setRevenueData] = useState(null)
  const [securityData, setSecurityData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      adminApi.getFinance().catch(() => ({ data: null })),
      adminApi.getRevenue().catch(() => ({ data: null })),
      adminApi.getSecurity().catch(() => ({ data: null })),
    ]).then(([finRes, revRes, secRes]) => {
      setFinanceData(finRes.data)
      setRevenueData(revRes.data)
      setSecurityData(secRes.data)
      setLoading(false)
    })
  }, [])

  const summary = financeData?.summary || {
    total_deposits: 0,
    total_withdrawals: 0,
    pending_withdrawals: 0,
    pending_withdrawals_amount: 0,
    escrow_balance: 0,
    net_revenue: 0,
  }

  const withdrawals = financeData?.withdrawals || []

  const tabs = [
    { id: 'cashflow', label: 'Cockpit financier', icon: DollarSign },
    { id: 'payouts', label: 'Payouts', icon: Banknote },
    { id: 'fraud', label: 'Fraude & anomalies', icon: Shield },
  ]

  const filteredWithdrawals = withdrawals.filter(w => {
    if (filterStatus !== 'all' && w.status !== filterStatus) return false
    if (search) {
      const q = search.toLowerCase()
      if (!w.user?.toLowerCase().includes(q) && !w.email?.toLowerCase().includes(q) && !String(w.id).includes(q)) return false
    }
    return true
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Finance"
        description="Cashflow, retraits, détection de fraude et passerelles de paiement"
        icon={DollarSign}
        actions={
          <button className="btn-secondary">
            <Download className="w-4 h-4" />
            Export comptable
          </button>
        }
      />

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
            {tab.id === 'payouts' && (
              <span className="badge bg-amber-100 text-amber-700 ml-1">{summary.pending_withdrawals}</span>
            )}
            {tab.id === 'fraud' && (
              <span className="badge bg-red-100 text-red-700 ml-1">{securityData?.summary?.disputed_orders || 0}</span>
            )}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-10 h-10 border-3 border-mantota-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
      <div className="animate-fade-in">
        {activeTab === 'cashflow' && <CashflowTab summary={summary} revenueData={revenueData} />}
        {activeTab === 'payouts' && (
          <PayoutsTab
            withdrawals={filteredWithdrawals}
            search={search}
            setSearch={setSearch}
            filterStatus={filterStatus}
            setFilterStatus={setFilterStatus}
            summary={summary}
          />
        )}
        {activeTab === 'fraud' && <FraudTab securityData={securityData} />}
      </div>
      )}
    </div>
  )
}

function CashflowTab({ summary, revenueData }) {
  const s = summary || { net_revenue: 0, escrow_balance: 0, total_deposits: 0, total_withdrawals: 0, pending_withdrawals: 0, pending_withdrawals_amount: 0 }
  const rev = revenueData || {}
  const revSummary = rev.summary || {}

  const cashflowData = (rev.series || []).map(d => ({
    day: d.date?.slice(5) || '',
    entrees: d.gross || 0,
    sorties: d.commission || 0,
  }))

  const revenueSources = [
    { name: 'Commissions', value: revSummary.total_commission || 0, color: '#0BBFA0' },
    { name: 'Markups passerelle', value: revSummary.mantota_markup || 0, color: '#8B5CF6' },
    { name: 'Frais de livraison', value: revSummary.total_delivery_fees || 0, color: '#FF6B35' },
    { name: 'Frais de passerelle', value: revSummary.gateway_fees || 0, color: '#F59E0B' },
  ].filter(r => r.value > 0)

  const totalRevenueSources = revenueSources.reduce((a, b) => a + b.value, 0)
  const projectedNet = Number(s.net_revenue || 0) - Number(s.pending_withdrawals_amount || 0)

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Liquidité plateforme" value={`${Number(s.net_revenue).toLocaleString()} FCFA`} icon={Wallet} color="mantota" />
        <StatCard label="Escrow actif" value={`${Number(s.escrow_balance).toLocaleString()} FCFA`} icon={Shield} color="amber" subtitle="Fonds séquestrés" />
        <StatCard label="Entrées (total)" value={`${Number(s.total_deposits).toLocaleString()} FCFA`} icon={ArrowUpRight} color="blue" />
        <StatCard label="Sorties (total)" value={`${Number(s.total_withdrawals).toLocaleString()} FCFA`} icon={ArrowDownRight} color="coral" />
      </div>

      {/* Cashflow chart */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-slate-900">Cashflow (30 derniers jours)</h3>
            <p className="text-xs text-slate-400 mt-0.5">Volume brute vs commissions</p>
          </div>
          <div className="flex items-center gap-3 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-mantota-500"></span>
              <span className="text-slate-500">Volume brut</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-coral-500"></span>
              <span className="text-slate-500">Commissions</span>
            </div>
          </div>
        </div>
        {cashflowData.length === 0 ? (
          <div className="text-center py-12 text-sm text-slate-400">Aucune donnée de cashflow disponible</div>
        ) : (
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={cashflowData}>
            <defs>
              <linearGradient id="colorEntrees" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0BBFA0" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#0BBFA0" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="colorSorties" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#FF6B35" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#FF6B35" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="day" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v / 1000}k`} />
            <Tooltip formatter={(value) => `${Number(value).toLocaleString()} FCFA`} contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
            <Area type="monotone" dataKey="entrees" stroke="#0BBFA0" strokeWidth={2.5} fill="url(#colorEntrees)" />
            <Area type="monotone" dataKey="sorties" stroke="#FF6B35" strokeWidth={2.5} fill="url(#colorSorties)" />
          </AreaChart>
        </ResponsiveContainer>
        )}
      </div>

      {/* Revenue breakdown + Projections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="font-semibold text-slate-900 mb-1">Revenus par source</h3>
          <p className="text-xs text-slate-400 mb-4">Cumul total</p>
          {revenueSources.length === 0 ? (
            <div className="text-center py-8 text-sm text-slate-400">Aucune donnée de revenu disponible</div>
          ) : (
            <>
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie data={revenueSources} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3}>
                    {revenueSources.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => `${Number(value).toLocaleString()} FCFA`} contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2 mt-2">
                {revenueSources.map((item, i) => (
                  <div key={i} className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: item.color }}></span>
                      <span className="text-slate-600">{item.name}</span>
                    </div>
                    <span className="font-semibold text-slate-900">{item.value.toLocaleString()} FCFA</span>
                  </div>
                ))}
                <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
                  <span className="font-semibold text-slate-700">Total</span>
                  <span className="font-bold text-mantota-600">{totalRevenueSources.toLocaleString()} FCFA</span>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="card p-6">
          <h3 className="font-semibold text-slate-900 mb-1">Projections</h3>
          <p className="text-xs text-slate-400 mb-4">Sorties prévues (7 prochains jours)</p>
          <div className="space-y-3">
            <div className="p-4 rounded-lg bg-amber-50 border border-amber-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-500" />
                  <span className="text-sm font-medium text-amber-700">Retraits en attente</span>
                </div>
                <span className="text-lg font-bold text-amber-700">{Number(s.pending_withdrawals_amount || 0).toLocaleString()} FCFA</span>
              </div>
              <p className="text-xs text-amber-600 mt-1">{s.pending_withdrawals} demandes à valider</p>
            </div>
            <div className="p-4 rounded-lg bg-blue-50 border border-blue-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 text-blue-500" />
                  <span className="text-sm font-medium text-blue-700">Escrow à libérer</span>
                </div>
                <span className="text-lg font-bold text-blue-700">{Number(s.escrow_balance || 0).toLocaleString()} FCFA</span>
              </div>
              <p className="text-xs text-blue-600 mt-1">Commandes en attente de confirmation</p>
            </div>
            <div className="p-4 rounded-lg bg-mantota-50 border border-mantota-100">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-mantota-600" />
                  <span className="text-sm font-medium text-mantota-700">Liquidité nette projetée</span>
                </div>
                <span className="text-lg font-bold text-mantota-700">{projectedNet.toLocaleString()} FCFA</span>
              </div>
              <p className="text-xs text-mantota-600 mt-1">Après sorties prévues</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function PayoutsTab({ withdrawals, search, setSearch, filterStatus, setFilterStatus, summary }) {
  const pendingCount = summary?.pending_withdrawals || 0
  const pendingAmount = summary?.pending_withdrawals_amount || 0
  const completedCount = withdrawals.filter(w => w.status === 'completed').length
  const rejectedCount = withdrawals.filter(w => w.status === 'rejected' || w.status === 'failed').length

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="En attente" value={pendingCount} icon={Clock} color="amber" />
        <StatCard label="Montant en attente" value={`${pendingAmount.toLocaleString()} FCFA`} icon={Banknote} color="coral" />
        <StatCard label="Validés" value={completedCount} icon={Check} color="mantota" />
        <StatCard label="Rejetés" value={rejectedCount} icon={X} color="red" />
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input type="text" placeholder="Rechercher user, email, ID..." value={search} onChange={e => setSearch(e.target.value)} className="input pl-9" />
          </div>
          <div className="flex items-center bg-slate-100 rounded-lg p-1">
            {['pending', 'completed', 'rejected', 'all'].map(s => (
              <button
                key={s}
                onClick={() => setFilterStatus(s)}
                className={clsx('px-3 py-1.5 rounded-md text-xs font-medium transition-colors capitalize',
                  filterStatus === s ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
                )}
              >
                {s === 'all' ? 'Tous' : s === 'pending' ? 'En attente' : s === 'completed' ? 'Validés' : 'Rejetés'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Withdrawals table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="table-header">ID</th>
                <th className="table-header">Utilisateur</th>
                <th className="table-header">Montant</th>
                <th className="table-header">Méthode</th>
                <th className="table-header">Pays</th>
                <th className="table-header">KYC</th>
                <th className="table-header">Date</th>
                <th className="table-header">Statut</th>
                <th className="table-header">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {withdrawals.length === 0 ? (
                <tr><td colSpan={9} className="text-center py-8 text-sm text-slate-400">Aucun retrait trouvé</td></tr>
              ) : withdrawals.map(w => (
                <tr key={w.id} className="table-row">
                  <td className="table-cell font-mono text-xs text-slate-500">{w.id}</td>
                  <td className="table-cell">
                    <div>
                      <p className="font-medium text-slate-900">{w.user}</p>
                      <p className="text-xs text-slate-400">{w.email}</p>
                    </div>
                  </td>
                  <td className="table-cell">
                    <span className="font-semibold text-slate-900">{w.amount.toLocaleString()}</span>
                    <span className="text-xs text-slate-400 ml-1">FCFA</span>
                  </td>
                  <td className="table-cell text-sm text-slate-600">{w.method}</td>
                  <td className="table-cell text-sm text-slate-600">{w.country}</td>
                  <td className="table-cell">
                    <Badge variant={w.kyc === 'verified' || w.kyc === 'approved' ? 'success' : w.kyc === 'rejected' ? 'danger' : 'warning'}>
                      {w.kyc || 'unknown'}
                    </Badge>
                  </td>
                  <td className="table-cell text-sm text-slate-500">{w.created_at ? new Date(w.created_at).toLocaleDateString('fr-FR') : '—'}</td>
                  <td className="table-cell">
                    <Badge variant={w.status === 'completed' ? 'success' : w.status === 'pending' ? 'warning' : 'danger'}>
                      {w.status === 'completed' ? 'Validé' : w.status === 'pending' ? 'En attente' : 'Rejeté'}
                    </Badge>
                  </td>
                  <td className="table-cell">
                    {w.status === 'pending' && (
                      <div className="flex items-center gap-1">
                        <button className="btn-ghost p-1.5 rounded-lg hover:bg-green-50 hover:text-green-600" title="Approuver">
                          <Check className="w-4 h-4" />
                        </button>
                        <button className="btn-ghost p-1.5 rounded-lg hover:bg-red-50 hover:text-red-600" title="Rejeter">
                          <X className="w-4 h-4" />
                        </button>
                        <button className="btn-ghost p-1.5 rounded-lg" title="Détails">
                          <Eye className="w-4 h-4" />
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

function FraudTab({ securityData }) {
  const sec = securityData || {}
  const secSummary = sec.summary || {}
  const disputes = sec.recent_disputes || []
  const banned = sec.recent_banned || []

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Commandes en litige" value={secSummary.disputed_orders || 0} icon={AlertTriangle} color="coral" />
        <StatCard label="Users bannis" value={secSummary.banned_users || 0} icon={Shield} color="red" />
        <StatCard label="Emails non vérifiés" value={secSummary.unverified_emails || 0} icon={Eye} color="amber" />
        <StatCard label="Téléphones non vérifiés" value={secSummary.unverified_phones || 0} icon={X} color="purple" />
      </div>

      {/* Disputes */}
      <div className="space-y-3">
        <h3 className="font-semibold text-slate-900">Commandes en litige</h3>
        {disputes.length === 0 ? (
          <div className="card p-8 text-center text-sm text-slate-400">Aucun litige actif</div>
        ) : disputes.map(d => (
          <div key={d.id} className="card p-5">
            <div className="flex items-start gap-4">
              <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0 bg-red-50 text-red-500">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2.5 mb-1">
                  <p className="font-semibold text-slate-900 font-mono text-sm">{d.reference}</p>
                  <Badge variant="danger">Litige</Badge>
                </div>
                <p className="text-sm text-slate-600">{d.dispute_reason || 'Raison non spécifiée'}</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                  <span>Client: <span className="font-medium text-slate-600">{d.customer}</span></span>
                  <span>{d.created_at ? new Date(d.created_at).toLocaleDateString('fr-FR') : '—'}</span>
                </div>
              </div>
              <button className="btn-secondary text-xs">
                <Eye className="w-3.5 h-3.5" />
                Examiner
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Banned users */}
      <div className="space-y-3">
        <h3 className="font-semibold text-slate-900">Utilisateurs bannis récemment</h3>
        {banned.length === 0 ? (
          <div className="card p-8 text-center text-sm text-slate-400">Aucun utilisateur banni récemment</div>
        ) : (
          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th className="table-header">Nom</th>
                    <th className="table-header">Email</th>
                    <th className="table-header">Rôle</th>
                    <th className="table-header">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {banned.map(u => (
                    <tr key={u.id} className="table-row">
                      <td className="table-cell font-medium text-slate-900">{u.name}</td>
                      <td className="table-cell text-sm text-slate-600">{u.email}</td>
                      <td className="table-cell text-sm text-slate-600">{u.role}</td>
                      <td className="table-cell text-sm text-slate-500">{u.deleted_at ? new Date(u.deleted_at).toLocaleDateString('fr-FR') : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Rules config */}
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Règles de détection configurables</h3>
        <div className="space-y-3">
          {[
            { label: 'Retrait > 3x moyenne habituelle', threshold: '3x', enabled: true },
            { label: 'Compte récent < 7 jours + retrait', threshold: '7 jours', enabled: true },
            { label: 'KYC non validé + activité financière', threshold: 'KYC != verified', enabled: true },
            { label: 'Multi-comptes même IP', threshold: '3 comptes / 1h', enabled: true },
            { label: 'Retrait immédiat après dépôt', threshold: '< 5 min', enabled: false },
          ].map((rule, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-slate-100">
              <div>
                <p className="text-sm font-medium text-slate-700">{rule.label}</p>
                <p className="text-xs text-slate-400">Seuil: {rule.threshold}</p>
              </div>
              <button className={clsx('relative w-11 h-6 rounded-full transition-colors', rule.enabled ? 'bg-mantota-500' : 'bg-slate-200')}>
                <span className={clsx('absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform', rule.enabled ? 'translate-x-5' : 'translate-x-0.5')} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
