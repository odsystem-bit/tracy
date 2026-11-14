import { useState, useEffect } from 'react'
import {
  Store, ShieldCheck, AlertTriangle, TrendingUp, TrendingDown,
  Search, Download, Eye, Star, Package, ShoppingBag, CheckCircle2,
  XCircle, Clock, Camera, Scale,
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'
import { adminApi } from '../api/admin'

const levelConfig = {
  excellent: { label: 'Excellent', variant: 'success', color: 'text-green-600', bg: 'bg-green-50', score: '≥ 80' },
  good: { label: 'Bon', variant: 'info', color: 'text-blue-600', bg: 'bg-blue-50', score: '60-79' },
  warning: { label: 'Alerte', variant: 'warning', color: 'text-amber-600', bg: 'bg-amber-50', score: '40-59' },
  risk: { label: 'À risque', variant: 'danger', color: 'text-red-600', bg: 'bg-red-50', score: '20-39' },
  suspended: { label: 'Suspendue', variant: 'danger', color: 'text-red-700', bg: 'bg-red-100', score: '< 20' },
}

function getLevel(score) {
  if (score >= 80) return 'excellent'
  if (score >= 60) return 'good'
  if (score >= 40) return 'warning'
  if (score >= 20) return 'risk'
  return 'suspended'
}

export default function ShopQuality() {
  const [search, setSearch] = useState('')
  const [filterLevel, setFilterLevel] = useState('all')
  const [selectedShop, setSelectedShop] = useState(null)
  const [data, setData] = useState([])
  const [summary, setSummary] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminApi.getShopQuality()
      .then(({ data }) => {
        setData(data.data || [])
        setSummary(data.summary || {})
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = data.filter(s => {
    const level = getLevel(s.quality_score)
    if (filterLevel !== 'all' && level !== filterLevel) return false
    if (search && !s.shop_name?.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Qualité des boutiques"
        description="Score de qualité automatique, authenticité des photos et conformité"
        icon={ShieldCheck}
        badge={<Badge variant="danger">{data.filter(s => getLevel(s.quality_score) === 'suspended' || getLevel(s.quality_score) === 'risk').length} critiques</Badge>}
        actions={<button className="btn-secondary"><Download className="w-4 h-4" />Export</button>}
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="Boutiques excellentes" value={data.filter(s => getLevel(s.quality_score) === 'excellent').length} icon={CheckCircle2} color="mantota" />
        <StatCard label="En alerte" value={data.filter(s => getLevel(s.quality_score) === 'warning').length} icon={AlertTriangle} color="amber" />
        <StatCard label="À risque" value={data.filter(s => getLevel(s.quality_score) === 'risk').length} icon={AlertTriangle} color="coral" />
        <StatCard label="Suspendues" value={data.filter(s => getLevel(s.quality_score) === 'suspended').length} icon={XCircle} color="red" />
        <StatCard label="Score moyen" value={`${summary.avg_quality || 0}/100`} icon={TrendingUp} color="blue" />
      </div>

      {/* Score distribution */}
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Distribution des scores</h3>
        {loading ? (
          <div className="flex items-center justify-center h-[200px]"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
        ) : (
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={[
            { level: 'Excellent', count: data.filter(s => getLevel(s.quality_score) === 'excellent').length, color: '#22C55E' },
            { level: 'Bon', count: data.filter(s => getLevel(s.quality_score) === 'good').length, color: '#3B82F6' },
            { level: 'Alerte', count: data.filter(s => getLevel(s.quality_score) === 'warning').length, color: '#F59E0B' },
            { level: 'À risque', count: data.filter(s => getLevel(s.quality_score) === 'risk').length, color: '#FF6B35' },
            { level: 'Suspendue', count: data.filter(s => getLevel(s.quality_score) === 'suspended').length, color: '#EF4444' },
          ]} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis type="number" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
            <YAxis type="category" dataKey="level" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} width={90} />
            <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
            <Bar dataKey="count" name="Boutiques" radius={[0, 4, 4, 0]} fill="#0BBFA0" />
          </BarChart>
        </ResponsiveContainer>
        )}
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input type="text" placeholder="Rechercher boutique ou vendeur..." value={search} onChange={e => setSearch(e.target.value)} className="input pl-9" />
          </div>
          <div className="flex items-center gap-1 flex-wrap">
            {['all', 'excellent', 'good', 'warning', 'risk', 'suspended'].map(l => (
              <button key={l} onClick={() => setFilterLevel(l)}
                className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  filterLevel === l ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                )}>
                {l === 'all' ? 'Toutes' : levelConfig[l]?.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Shop cards */}
      {loading ? (
        <div className="flex items-center justify-center py-12"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center text-slate-400">Aucune boutique trouvée</div>
      ) : (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map(shop => {
          const level = getLevel(shop.quality_score)
          const cfg = levelConfig[level]
          return (
            <div key={shop.id} className="card card-hover p-5 cursor-pointer" onClick={() => setSelectedShop(shop)}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-xl bg-slate-100 flex items-center justify-center">
                    <Store className="w-5 h-5 text-slate-500" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-900 text-sm">{shop.shop_name}</p>
                    <p className="text-xs text-slate-400 capitalize">{shop.bot_plan || 'free'} · {shop.country || 'N/A'}</p>
                  </div>
                </div>
                <Badge variant={cfg.variant}>{cfg.label}</Badge>
              </div>

              {/* Score */}
              <div className={clsx('p-4 rounded-xl mb-3', cfg.bg)}>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-slate-600">Score qualité</span>
                  <span className={clsx('text-2xl font-bold', cfg.color)}>{shop.quality_score}<span className="text-sm text-slate-400">/100</span></span>
                </div>
                <div className="w-full h-2 rounded-full bg-white/50 overflow-hidden">
                  <div className={clsx('h-full rounded-full transition-all',
                    level === 'excellent' ? 'bg-green-500' :
                    level === 'good' ? 'bg-blue-500' :
                    level === 'warning' ? 'bg-amber-500' :
                    level === 'risk' ? 'bg-coral-500' : 'bg-red-500'
                  )} style={{ width: `${shop.quality_score}%` }}></div>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="p-2 rounded-lg bg-slate-50 text-center">
                  <Package className="w-3.5 h-3.5 text-slate-400 mx-auto mb-1" />
                  <p className="text-sm font-bold text-slate-900">{shop.total_products}</p>
                  <p className="text-[10px] text-slate-400">produits</p>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 text-center">
                  <ShoppingBag className="w-3.5 h-3.5 text-slate-400 mx-auto mb-1" />
                  <p className="text-sm font-bold text-slate-900">{shop.total_orders}</p>
                  <p className="text-[10px] text-slate-400">commandes</p>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 text-center">
                  <CheckCircle2 className="w-3.5 h-3.5 text-green-500 mx-auto mb-1" />
                  <p className="text-sm font-bold text-green-600">{shop.delivery_rate}%</p>
                  <p className="text-[10px] text-slate-400">livraison</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
      )}

      {/* Recent signals */}
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Litiges récents</h3>
        {loading ? (
          <div className="flex items-center justify-center py-8"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
        ) : (
        <div className="space-y-2">
          {filtered.filter(s => s.disputed > 0).slice(0, 8).map(shop => (
            <div key={shop.id} className="flex items-center gap-3 p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-red-50 text-red-500">
                <TrendingDown className="w-4 h-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900">{shop.shop_name}</p>
                <p className="text-xs text-slate-400">{shop.disputed} litige(s) · {shop.dispute_rate}% taux</p>
              </div>
              <span className="text-sm font-bold text-red-500">{shop.disputed}</span>
            </div>
          ))}
          {filtered.filter(s => s.disputed > 0).length === 0 && (
            <div className="text-center py-8 text-sm text-slate-400">Aucun litige récent</div>
          )}
        </div>
        )}
      </div>

      {/* Detail modal */}
      {selectedShop && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={() => setSelectedShop(null)}>
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-slate-100 flex items-center justify-center">
                  <Store className="w-6 h-6 text-slate-500" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900">{selectedShop.shop_name}</h2>
                  <p className="text-sm text-slate-400 capitalize">{selectedShop.bot_plan} · {selectedShop.country}</p>
                </div>
              </div>
              <Badge variant={levelConfig[getLevel(selectedShop.quality_score)].variant}>{levelConfig[getLevel(selectedShop.quality_score)].label}</Badge>
            </div>

            <div className={clsx('p-6 rounded-xl mb-6', levelConfig[getLevel(selectedShop.quality_score)].bg)}>
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-medium text-slate-600">Score de qualité</span>
                <span className={clsx('text-4xl font-bold', levelConfig[getLevel(selectedShop.quality_score)].color)}>{selectedShop.quality_score}<span className="text-lg text-slate-400">/100</span></span>
              </div>
              <div className="w-full h-3 rounded-full bg-white/50 overflow-hidden">
                <div className={clsx('h-full rounded-full transition-all',
                  getLevel(selectedShop.quality_score) === 'excellent' ? 'bg-green-500' :
                  getLevel(selectedShop.quality_score) === 'good' ? 'bg-blue-500' :
                  getLevel(selectedShop.quality_score) === 'warning' ? 'bg-amber-500' :
                  getLevel(selectedShop.quality_score) === 'risk' ? 'bg-coral-500' : 'bg-red-500'
                )} style={{ width: `${selectedShop.quality_score}%` }}></div>
              </div>
              <div className="grid grid-cols-3 gap-3 mt-4">
                <div className="text-center">
                  <p className="text-xs text-slate-400">Produits</p>
                  <p className="text-lg font-bold text-slate-900">{selectedShop.total_products}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-slate-400">Commandes</p>
                  <p className="text-lg font-bold text-slate-900">{selectedShop.total_orders}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-slate-400">Livraison</p>
                  <p className="text-lg font-bold text-green-600">{selectedShop.delivery_rate}%</p>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3">
              {getLevel(selectedShop.quality_score) === 'suspended' && (
                <button className="btn-primary">
                  <CheckCircle2 className="w-4 h-4" />
                  Réactiver la boutique
                </button>
              )}
              {getLevel(selectedShop.quality_score) === 'risk' && (
                <button className="btn-danger">
                  <XCircle className="w-4 h-4" />
                  Suspendre
                </button>
              )}
              <button className="btn-secondary">
                <Scale className="w-4 h-4" />
                Historique conformité
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
