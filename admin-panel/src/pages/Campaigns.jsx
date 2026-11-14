import { useState } from 'react'
import {
  Megaphone, Target, DollarSign, Eye, TrendingUp, Plus,
  Search, Download, Play, Pause, BarChart3, Users,
} from 'lucide-react'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'

const mockCampaigns = [
  { id: 'CMP-001', name: 'Soldes Cotonou', vendor: 'Boutique Elite', budget: 50000, spent: 32000, impressions: 12450, clicks: 892, conversions: 45, revenue: 280000, status: 'active', startDate: '20 Aoû', endDate: '30 Aoû' },
  { id: 'CMP-002', name: 'Back to School', vendor: 'TechStore BJ', budget: 30000, spent: 28000, impressions: 8900, clicks: 567, conversions: 28, revenue: 145000, status: 'active', startDate: '15 Aoû', endDate: '28 Aoû' },
  { id: 'CMP-003', name: 'Fashion Week Abidjan', vendor: 'Abidjan Market', budget: 80000, spent: 45000, impressions: 15600, clicks: 1234, conversions: 67, revenue: 420000, status: 'active', startDate: '22 Aoû', endDate: '05 Sep' },
  { id: 'CMP-004', name: 'Soldes Dakar', vendor: 'Dakar Store', budget: 60000, spent: 60000, impressions: 18200, clicks: 1456, conversions: 89, revenue: 560000, status: 'completed', startDate: '01 Aoû', endDate: '15 Aoû' },
  { id: 'CMP-005', name: 'Lagos Tech Promo', vendor: 'Lagos Gadgets', budget: 25000, spent: 12000, impressions: 4500, clicks: 234, conversions: 12, revenue: 67000, status: 'paused', startDate: '24 Aoû', endDate: '10 Sep' },
]

const mockPerf = [
  { day: 'Lun', impressions: 3200, clicks: 234, conversions: 12 },
  { day: 'Mar', impressions: 4100, clicks: 312, conversions: 18 },
  { day: 'Mer', impressions: 3800, clicks: 289, conversions: 15 },
  { day: 'Jeu', impressions: 5200, clicks: 412, conversions: 24 },
  { day: 'Ven', impressions: 6800, clicks: 534, conversions: 32 },
  { day: 'Sam', impressions: 7200, clicks: 578, conversions: 38 },
  { day: 'Dim', impressions: 4500, clicks: 345, conversions: 21 },
]

export default function Campaigns() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  const filtered = mockCampaigns.filter(c => {
    if (filterStatus !== 'all' && c.status !== filterStatus) return false
    if (search && !c.name.toLowerCase().includes(search.toLowerCase()) && !c.vendor.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  const totals = {
    budget: mockCampaigns.reduce((a, b) => a + b.budget, 0),
    spent: mockCampaigns.reduce((a, b) => a + b.spent, 0),
    conversions: mockCampaigns.reduce((a, b) => a + b.conversions, 0),
    revenue: mockCampaigns.reduce((a, b) => a + b.revenue, 0),
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Campagnes"
        description="Gestion et analytics des campagnes publicitaires des vendeurs"
        icon={Megaphone}
        actions={<button className="btn-primary"><Plus className="w-4 h-4" />Nouvelle campagne</button>}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Budget total" value={`${totals.budget.toLocaleString()} FCFA`} icon={DollarSign} color="mantota" />
        <StatCard label="Dépensé" value={`${totals.spent.toLocaleString()} FCFA`} icon={Target} color="coral" />
        <StatCard label="Conversions" value={totals.conversions} icon={TrendingUp} color="blue" />
        <StatCard label="ROAS moyen" value="4.2x" icon={BarChart3} color="purple" trend="up" trendValue="+0.8x" />
      </div>

      {/* Performance chart */}
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-1">Performance campagnes (7j)</h3>
        <p className="text-xs text-slate-400 mb-4">Impressions, clics et conversions par jour</p>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={mockPerf}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis dataKey="day" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
            <Bar dataKey="impressions" name="Impressions" fill="#E2E8F0" radius={[4, 4, 0, 0]} />
            <Bar dataKey="clicks" name="Clics" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="conversions" name="Conversions" fill="#0BBFA0" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input type="text" placeholder="Rechercher campagne ou vendeur..." value={search} onChange={e => setSearch(e.target.value)} className="input pl-9" />
          </div>
          <div className="flex items-center gap-1">
            {['all', 'active', 'paused', 'completed'].map(s => (
              <button key={s} onClick={() => setFilterStatus(s)}
                className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  filterStatus === s ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                )}>
                {s === 'all' ? 'Toutes' : s === 'active' ? 'Actives' : s === 'paused' ? 'En pause' : 'Terminées'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Campaign table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="table-header">Campagne</th>
                <th className="table-header">Vendeur</th>
                <th className="table-header">Budget</th>
                <th className="table-header">Dépensé</th>
                <th className="table-header">Impressions</th>
                <th className="table-header">Clics</th>
                <th className="table-header">Conv.</th>
                <th className="table-header">Revenus</th>
                <th className="table-header">ROAS</th>
                <th className="table-header">Statut</th>
                <th className="table-header"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {filtered.map(c => {
                const roas = (c.revenue / c.spent).toFixed(1)
                const budgetUsed = Math.round((c.spent / c.budget) * 100)
                return (
                  <tr key={c.id} className="table-row">
                    <td className="table-cell">
                      <p className="font-medium text-slate-900 text-sm">{c.name}</p>
                      <p className="text-xs text-slate-400 font-mono">{c.id}</p>
                    </td>
                    <td className="table-cell text-sm text-slate-600">{c.vendor}</td>
                    <td className="table-cell text-sm text-slate-600">{c.budget.toLocaleString()} FCFA</td>
                    <td className="table-cell">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                          <div className={clsx('h-full rounded-full', budgetUsed >= 100 ? 'bg-red-500' : budgetUsed >= 80 ? 'bg-amber-500' : 'bg-mantota-500')} style={{ width: `${Math.min(budgetUsed, 100)}%` }}></div>
                        </div>
                        <span className="text-xs text-slate-500">{c.spent.toLocaleString()}</span>
                      </div>
                    </td>
                    <td className="table-cell text-sm text-slate-600">{c.impressions.toLocaleString()}</td>
                    <td className="table-cell text-sm text-slate-600">{c.clicks}</td>
                    <td className="table-cell text-sm font-semibold text-slate-900">{c.conversions}</td>
                    <td className="table-cell text-sm font-semibold text-mantota-600">{c.revenue.toLocaleString()} FCFA</td>
                    <td className="table-cell">
                      <span className={clsx('text-sm font-bold', Number(roas) >= 3 ? 'text-green-600' : Number(roas) >= 1.5 ? 'text-amber-600' : 'text-red-500')}>{roas}x</span>
                    </td>
                    <td className="table-cell">
                      <Badge variant={c.status === 'active' ? 'success' : c.status === 'paused' ? 'warning' : 'neutral'}>
                        {c.status === 'active' ? 'Active' : c.status === 'paused' ? 'En pause' : 'Terminée'}
                      </Badge>
                    </td>
                    <td className="table-cell">
                      <button className="btn-ghost p-1.5 rounded-lg">
                        {c.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
