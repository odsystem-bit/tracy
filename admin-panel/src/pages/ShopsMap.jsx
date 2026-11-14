import { useState, useEffect, useMemo } from 'react'
import {
  Store, MapPin, Filter, Download, Search, ChevronDown,
  Package, ShoppingBag, ShieldCheck, Star, TrendingUp,
} from 'lucide-react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import PageHeader from '../components/PageHeader'
import Badge from '../components/Badge'
import StatCard from '../components/StatCard'
import clsx from 'clsx'
import { adminApi } from '../api/admin'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
})

const planColors = {
  pro: '#8B5CF6',
  standard: '#3B82F6',
  starter: '#0BBFA0',
  free: '#94A3B8',
}

function makeIcon(color) {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="background:${color};width:14px;height:14px;border:3px solid white;border-radius:50%;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>`,
    iconSize: [14, 14],
    iconAnchor: [7, 7],
  })
}

export default function ShopsMap() {
  const [filterPlan, setFilterPlan] = useState('all')
  const [filterCountry, setFilterCountry] = useState('all')
  const [search, setSearch] = useState('')
  const [selectedShop, setSelectedShop] = useState(null)
  const [viewMode, setViewMode] = useState('map')
  const [shops, setShops] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    adminApi.getShopsMap()
      .then(({ data }) => setShops(data.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const filtered = useMemo(() => {
    return shops.filter(s => {
      if (filterPlan !== 'all' && s.bot_plan !== filterPlan) return false
      if (filterCountry !== 'all' && s.country !== filterCountry) return false
      if (search) {
        const q = search.toLowerCase()
        if (!s.shop_name?.toLowerCase().includes(q) && !s.country?.toLowerCase().includes(q)) return false
      }
      return true
    })
  }, [shops, filterPlan, filterCountry, search])

  const countries = [...new Set(shops.map(s => s.country).filter(Boolean))]

  const stats = {
    total: shops.length,
    active: shops.filter(s => s.bot_status === 'active').length,
    pro: shops.filter(s => s.bot_plan === 'pro').length,
    starter: shops.filter(s => s.bot_plan === 'starter').length,
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Carte des boutiques"
        description="Visualisation géographique de toutes les boutiques MANTOTA"
        icon={Store}
        badge={<Badge variant="info">{filtered.length} boutiques</Badge>}
        actions={
          <>
            <div className="flex items-center bg-slate-100 rounded-lg p-1">
              <button
                onClick={() => setViewMode('map')}
                className={clsx('px-3 py-1.5 rounded-md text-xs font-medium transition-colors', viewMode === 'map' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500')}
              >
                Carte
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={clsx('px-3 py-1.5 rounded-md text-xs font-medium transition-colors', viewMode === 'list' ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500')}
              >
                Liste
              </button>
            </div>
            <button className="btn-secondary">
              <Download className="w-4 h-4" />
              Export CSV
            </button>
          </>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total boutiques" value={stats.total} icon={Store} color="mantota" />
        <StatCard label="Actives" value={stats.active} icon={ShieldCheck} color="blue" />
        <StatCard label="Plan Starter" value={stats.starter} icon={Star} color="amber" />
        <StatCard label="Plan Pro" value={stats.pro} icon={Star} color="purple" />
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Rechercher boutique, vendeur, ville..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-9"
            />
          </div>
          <FilterSelect label="Plan" value={filterPlan} onChange={setFilterPlan} options={[
            { value: 'all', label: 'Tous les plans' },
            { value: 'pro', label: 'Pro' },
            { value: 'standard', label: 'Standard' },
            { value: 'starter', label: 'Starter' },
            { value: 'free', label: 'Free' },
          ]} />
          <FilterSelect label="Pays" value={filterCountry} onChange={setFilterCountry} options={[
            { value: 'all', label: 'Tous les pays' },
            ...countries.map(c => ({ value: c, label: c })),
          ]} />
        </div>
        {/* Legend */}
        <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-100">
          <span className="text-xs text-slate-400 font-medium">Légende:</span>
          {Object.entries(planColors).map(([plan, color]) => (
            <div key={plan} className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full" style={{ background: color }}></span>
              <span className="text-xs text-slate-500 capitalize">{plan}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Map or List */}
      {loading ? (
        <div className="card p-12 flex items-center justify-center"><div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div></div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center text-slate-400">Aucune boutique avec coordonnées GPS. Les vendeurs doivent renseigner leur adresse dans l'app.</div>
      ) : viewMode === 'map' ? (
        <div className="card overflow-hidden">
          <MapContainer
            center={[8.5, 2.5]}
            zoom={5}
            style={{ height: '600px', width: '100%' }}
            scrollWheelZoom
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; OpenStreetMap'
            />
            {filtered.map(shop => (
              <Marker
                key={shop.id}
                position={[shop.latitude, shop.longitude]}
                icon={makeIcon(planColors[shop.bot_plan] || planColors.free)}
                eventHandlers={{ click: () => setSelectedShop(shop) }}
              >
                <Popup>
                  <div className="min-w-[220px]">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold" style={{ background: planColors[shop.bot_plan] || planColors.free }}>
                        {shop.shop_name?.charAt(0)}
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900 text-sm">{shop.shop_name}</p>
                        <p className="text-xs text-slate-400">{shop.bot_plan}</p>
                      </div>
                    </div>
                    <div className="space-y-1 text-xs">
                      <p><span className="text-slate-400">Pays:</span> {shop.country || 'N/A'}</p>
                      <p><span className="text-slate-400">Adresse:</span> {shop.address || 'N/A'}</p>
                      <p><span className="text-slate-400">Plan:</span> <span className="capitalize font-medium">{shop.bot_plan || 'free'}</span></p>
                      <p><span className="text-slate-400">Téléphone:</span> {shop.phone || 'N/A'}</p>
                      <p><span className="text-slate-400">Statut:</span> {shop.bot_status || 'N/A'}</p>
                    </div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(shop => (
            <div key={shop.id} className="card card-hover p-5 cursor-pointer" onClick={() => setSelectedShop(shop)}>
              <div className="flex items-start gap-3 mb-3">
                <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white font-bold shrink-0" style={{ background: planColors[shop.bot_plan] || planColors.free }}>
                  {shop.shop_name?.charAt(0) || '?'}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-slate-900 truncate">{shop.shop_name}</p>
                  <p className="text-xs text-slate-400 truncate capitalize">{shop.bot_plan || 'free'} · {shop.bot_status || 'N/A'}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 mt-3 pt-3 border-t border-slate-50">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <span className="text-xs text-slate-500">{shop.address || shop.country || 'N/A'}</span>
                <span className="ml-auto badge capitalize" style={{ background: `${planColors[shop.bot_plan] || planColors.free}20`, color: planColors[shop.bot_plan] || planColors.free }}>
                  {shop.bot_plan || 'free'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function FilterSelect({ label, value, onChange, options }) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="input pr-8 py-2.5 appearance-none cursor-pointer min-w-[140px]"
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
      <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
    </div>
  )
}
