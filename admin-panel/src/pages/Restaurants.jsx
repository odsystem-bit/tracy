import { useState, useEffect } from 'react'
import {
  Store, Search, Eye, CheckCircle2, Clock,
  TrendingUp, Utensils, Package,
} from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import { adminApi } from '../api/admin'

const typeLabels = {
  restaurant_online: 'En ligne',
  restaurant_physical: 'Physique',
}

export default function Restaurants() {
  const [search, setSearch] = useState('')
  const [filterTab, setFilterTab] = useState('all')
  const [restaurants, setRestaurants] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(null)

  useEffect(() => {
    setLoading(true)
    adminApi.getRestaurants({ per_page: 50, search })
      .then(res => {
        setRestaurants(res.data.data || [])
        setLoading(false)
      })
      .catch(() => {
        setRestaurants([])
        setLoading(false)
      })
  }, [search])

  const filtered = restaurants.filter(r => {
    if (filterTab === 'active' && r.bot_status !== 'active') return false
    if (filterTab === 'inactive' && r.bot_status === 'active') return false
    return true
  })

  const stats = {
    total: restaurants.length,
    active: restaurants.filter(r => r.bot_status === 'active').length,
    orders: restaurants.reduce((sum, r) => sum + (r.total_orders || 0), 0),
    delivered: restaurants.reduce((sum, r) => sum + (r.delivered_orders || 0), 0),
  }

  if (selected) {
    return (
      <div className="space-y-6">
        <button onClick={() => setSelected(null)} className="btn-secondary">
          ← Retour
        </button>
        <div className="card p-6">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-xl font-bold text-slate-900">{selected.shop_name}</h2>
              <p className="text-sm text-slate-500 mt-1">
                {typeLabels[selected.shop_type] || selected.shop_type} · {selected.address || '—'}
              </p>
              <p className="text-sm text-slate-500">{selected.phone || '—'}</p>
            </div>
            <Badge variant={selected.bot_status === 'active' ? 'success' : 'neutral'}>
              {selected.bot_status === 'active' ? 'Actif' : 'Inactif'}
            </Badge>
          </div>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
            <StatCard label="Commandes totales" value={selected.total_orders || 0} icon={Package} color="blue" />
            <StatCard label="Livrées" value={selected.delivered_orders || 0} icon={CheckCircle2} color="mantota" />
            <StatCard label="Taux livraison" value={`${Math.round((selected.delivered_orders / Math.max(selected.total_orders, 1)) * 100)}%`} icon={TrendingUp} color="purple" />
            <StatCard label="Statut" value={selected.bot_status || '—'} icon={Clock} color="amber" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Restaurants"
        subtitle="Gestion des restaurants connectés à Tracy Core"
      />

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total restaurants" value={stats.total} icon={Store} color="mantota" />
        <StatCard label="Actifs" value={stats.active} icon={CheckCircle2} color="blue" />
        <StatCard label="Commandes" value={stats.orders} icon={Package} color="coral" />
        <StatCard label="Livrées" value={stats.delivered} icon={Utensils} color="purple" />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Rechercher un restaurant..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>
        <div className="flex items-center gap-2">
          {['all', 'active', 'inactive'].map(tab => (
            <button
              key={tab}
              onClick={() => setFilterTab(tab)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                filterTab === tab
                  ? 'bg-mantota-500 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {tab === 'all' ? 'Tous' : tab === 'active' ? 'Actifs' : 'Inactifs'}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="w-10 h-10 border-3 border-mantota-500 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Restaurant</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Type</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Contact</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Commandes</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Statut</th>
                  <th className="text-right px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map(r => (
                  <tr key={r.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-mantota-50 flex items-center justify-center shrink-0">
                          <Utensils className="w-4 h-4 text-mantota-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-900">{r.shop_name}</p>
                          <p className="text-xs text-slate-400">{r.address || '—'}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-600">{typeLabels[r.shop_type] || r.shop_type || '—'}</span>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-600">{r.phone || '—'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm font-medium text-slate-900">{r.total_orders || 0}</p>
                      <p className="text-xs text-slate-400">{r.delivered_orders || 0} livrées</p>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={r.bot_status === 'active' ? 'success' : 'neutral'}>
                        {r.bot_status === 'active' ? 'Actif' : 'Inactif'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setSelected(r)}
                        className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-500"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && (
              <div className="text-center py-12 text-slate-400 text-sm">
                Aucun restaurant trouvé
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
