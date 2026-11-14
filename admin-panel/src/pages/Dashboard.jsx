import { useEffect, useState } from 'react'
import {
  Users, Store, ShoppingBag, DollarSign, AlertTriangle,
  Clock, Activity, Package, MapPin,
} from 'lucide-react'
import StatCard from '../components/StatCard'
import ShopMap from '../components/ShopMap'
import Badge from '../components/Badge'
import { adminApi } from '../api/admin'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [feed, setFeed] = useState([])
  const [shops, setShops] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      adminApi.getDashboard().catch(() => ({ data: {} })),
      adminApi.getLiveFeed().catch(() => ({ data: { data: [] } })),
      adminApi.getShopsMap().catch(() => ({ data: { data: [] } })),
    ]).then(([dashRes, feedRes, shopsRes]) => {
      setData(dashRes.data)
      setFeed(feedRes.data?.data || [])
      setShops(shopsRes.data?.data || [])
      setLoading(false)
    })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-10 h-10 border-3 border-mantota-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  const k = data || {}
  const kpis = {
    totalUsers: k.total_users ?? 0,
    totalVendors: k.total_vendors ?? 0,
    totalOrders: k.total_orders ?? 0,
    totalRevenue: k.total_revenue ?? 0,
    pendingOrders: k.pending_orders ?? 0,
    openDisputes: k.open_disputes ?? 0,
    totalProducts: k.total_products ?? 0,
    totalWithdrawals: k.total_withdrawals ?? 0,
  }
  const recentUsers = k.recent_users || []
  const recentOrders = k.recent_orders || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500 mt-0.5">Vue d'ensemble de la plateforme MANTOTA</p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="success">
            <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></span>
            Temps réel
          </Badge>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Utilisateurs"
          value={kpis.totalUsers?.toLocaleString() || '0'}
          icon={Users}
          color="mantota"
        />
        <StatCard
          label="Boutiques actives"
          value={kpis.totalVendors?.toLocaleString() || '0'}
          icon={Store}
          color="blue"
        />
        <StatCard
          label="Commandes"
          value={kpis.totalOrders?.toLocaleString() || '0'}
          icon={ShoppingBag}
          color="coral"
        />
        <StatCard
          label="Revenus"
          value={`${Number(kpis.totalRevenue || 0).toLocaleString()} FCFA`}
          icon={DollarSign}
          color="purple"
        />
      </div>

      {/* Map + Revenue chart */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map — 2/3 width */}
        <div className="lg:col-span-2 card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-mantota-500" />
                Carte des boutiques
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {shops.length} boutiques géolocalisées
              </p>
            </div>
            <Badge variant="info">{shops.length} marqueurs</Badge>
          </div>
          <ShopMap shops={shops} height="380px" />
          {shops.length === 0 && (
            <p className="text-center text-sm text-slate-400 mt-2">Aucune boutique géolocalisée pour le moment</p>
          )}
        </div>

        {/* Revenue breakdown — 1/3 width */}
        <div className="card p-5">
          <h3 className="font-semibold text-slate-900 mb-1">Alertes & Statuts</h3>
          <p className="text-xs text-slate-400 mb-4">Indicateurs en temps réel</p>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg border border-amber-100 bg-amber-50">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-amber-500" />
                <span className="text-sm font-medium text-amber-700">Commandes en attente</span>
              </div>
              <span className="text-lg font-bold text-amber-700">{kpis.pendingOrders}</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg border border-red-100 bg-red-50">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-red-500" />
                <span className="text-sm font-medium text-red-700">Litiges ouverts</span>
              </div>
              <span className="text-lg font-bold text-red-700">{kpis.openDisputes}</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg border border-blue-100 bg-blue-50">
              <div className="flex items-center gap-2">
                <Package className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-medium text-blue-700">Produits totaux</span>
              </div>
              <span className="text-lg font-bold text-blue-700">{kpis.totalProducts}</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg border border-purple-100 bg-purple-50">
              <div className="flex items-center gap-2">
                <DollarSign className="w-4 h-4 text-purple-500" />
                <span className="text-sm font-medium text-purple-700">Retraits totaux</span>
              </div>
              <span className="text-lg font-bold text-purple-700">{Number(kpis.totalWithdrawals).toLocaleString()} FCFA</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent users + Recent orders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-5">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2 mb-4">
            <Users className="w-4 h-4 text-mantota-500" />
            Nouveaux utilisateurs
          </h3>
          {recentUsers.length === 0 ? (
            <div className="text-center py-8 text-sm text-slate-400">Aucun utilisateur récent</div>
          ) : (
            <div className="space-y-3">
              {recentUsers.slice(0, 6).map((u, i) => (
                <div key={i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center shrink-0">
                    <Users className="w-3.5 h-3.5 text-slate-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-700 truncate">{u.name || u.email || '—'}</p>
                    <p className="text-xs text-slate-400">{u.role || 'user'} · {u.created_at ? new Date(u.created_at).toLocaleDateString('fr-FR') : '—'}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card p-5">
          <h3 className="font-semibold text-slate-900 flex items-center gap-2 mb-4">
            <ShoppingBag className="w-4 h-4 text-coral-500" />
            Commandes récentes
          </h3>
          {recentOrders.length === 0 ? (
            <div className="text-center py-8 text-sm text-slate-400">Aucune commande récente</div>
          ) : (
            <div className="space-y-3">
              {recentOrders.slice(0, 6).map((o, i) => (
                <div key={i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors">
                  <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center shrink-0">
                    <ShoppingBag className="w-3.5 h-3.5 text-slate-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-700 truncate">{o.order_number || o.id || '—'} · {o.status || '—'}</p>
                    <p className="text-xs text-slate-400">{o.total ? Number(o.total).toLocaleString() : '—'} FCFA · {o.created_at ? new Date(o.created_at).toLocaleDateString('fr-FR') : '—'}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Live feed */}
      <div className="card p-5">
        <h3 className="font-semibold text-slate-900 flex items-center gap-2 mb-4">
          <Activity className="w-4 h-4 text-mantota-500" />
          Activité récente (live feed)
        </h3>
        {feed.length === 0 ? (
          <div className="text-center py-8 text-sm text-slate-400">Aucune activité récente</div>
        ) : (
          <div className="space-y-3">
            {feed.slice(0, 8).map((act, i) => (
              <div key={i} className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-50 transition-colors">
                <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center shrink-0">
                  <Activity className="w-3.5 h-3.5 text-slate-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 truncate">{act.message || act.type}</p>
                  <p className="text-xs text-slate-400">{act.type} · {act.time ? new Date(act.time).toLocaleTimeString() : ''}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
