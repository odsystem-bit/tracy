import { useState, useEffect } from 'react'
import {
  Globe2, MapPin, Users, Store, DollarSign, TrendingUp,
  ShoppingBag, ArrowUpRight, Download, Search,
} from 'lucide-react'
import {
  BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'
import { adminApi } from '../api/admin'

export default function Countries() {
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('revenue')
  const [data, setData] = useState([])
  const [summary, setSummary] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminApi.getCountries()
      .then(({ data }) => {
        setData(data.data || [])
        setSummary(data.summary || {})
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = data
    .filter(c => !search || (c.country || '').toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => (b[sortBy] || 0) - (a[sortBy] || 0))

  return (
    <div className="space-y-6">
      <PageHeader
        title="Performance par pays"
        description="Revenus, utilisateurs et opportunités d'expansion par marché"
        icon={Globe2}
        actions={
          <button className="btn-secondary">
            <Download className="w-4 h-4" />
            Export
          </button>
        }
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Pays actifs" value={summary.total_countries || 0} icon={Globe2} color="mantota" />
        <StatCard label="Total users" value={(summary.total_users || 0).toLocaleString()} icon={Users} color="blue" />
        <StatCard label="Total commandes" value={summary.total_orders || 0} icon={ShoppingBag} color="coral" />
        <StatCard label="Revenus totaux" value={`${((data.reduce((a, b) => a + (b.revenue || 0), 0)) / 1000000).toFixed(1)}M FCFA`} icon={DollarSign} color="purple" />
      </div>

      {/* Top countries bar chart */}
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-1">Revenus par pays</h3>
        <p className="text-xs text-slate-400 mb-4">Comparaison des marchés</p>
        {loading ? (
          <div className="flex items-center justify-center h-[300px]"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
        ) : data.length === 0 ? (
          <div className="h-[300px] flex items-center justify-center text-sm text-slate-400">Aucune donnée par pays</div>
        ) : (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={filtered.slice(0, 9)} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis type="number" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} tickFormatter={(v) => `${v / 1000}k`} />
            <YAxis type="category" dataKey="country" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} width={100} />
            <Tooltip formatter={(value) => `${Number(value).toLocaleString()} FCFA`} contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
            <Bar dataKey="revenue" fill="#0BBFA0" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
        )}
      </div>

      {/* Search + sort */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input type="text" placeholder="Rechercher un pays..." value={search} onChange={e => setSearch(e.target.value)} className="input pl-9" />
          </div>
          <div className="flex items-center gap-1">
            {[
              { key: 'revenue', label: 'Revenus' },
              { key: 'users', label: 'Users' },
              { key: 'orders', label: 'Commandes' },
            ].map(s => (
              <button key={s.key} onClick={() => setSortBy(s.key)}
                className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  sortBy === s.key ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                )}>
                {s.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Country cards */}
      {loading ? (
        <div className="flex items-center justify-center py-12"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center text-slate-400">Aucun pays trouvé</div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((country, i) => (
          <div key={i} className="card card-hover p-5">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">🌍</span>
                <div>
                  <p className="font-semibold text-slate-900">{country.country}</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-3">
              <div className="p-2.5 rounded-lg bg-slate-50">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider">Utilisateurs</p>
                <p className="text-lg font-bold text-slate-900">{(country.users || 0).toLocaleString()}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider">Commandes</p>
                <p className="text-lg font-bold text-slate-900">{country.orders || 0}</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider">Revenus</p>
                <p className="text-lg font-bold text-slate-900">{((country.revenue || 0) / 1000).toFixed(0)}k</p>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-50">
                <p className="text-[10px] text-slate-400 uppercase tracking-wider">Panier moyen</p>
                <p className="text-lg font-bold text-slate-900">{country.orders > 0 ? Math.round(country.revenue / country.orders).toLocaleString() : 0}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      )}
    </div>
  )
}
