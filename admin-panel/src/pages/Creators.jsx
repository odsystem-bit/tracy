import { useState } from 'react'
import {
  Sparkles, TrendingUp, DollarSign, Eye, Heart, Users,
  Star, Award, Download, Search, ChevronDown,
  Camera, Video, Share2, Music,
} from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'

const mockCreators = [
  { id: 1, name: 'Aminata Diallo', email: 'aminata.d@gmail.com', country: 'Côte d\'Ivoire', tier: 'gold', followers: 245000, engagement: 8.2, earnings: 890000, services: 12, rating: 4.9, status: 'active', platforms: ['instagram', 'youtube'] },
  { id: 2, name: 'Grace Mensah', email: 'grace.m@gmail.com', country: 'Ghana', tier: 'gold', followers: 180000, engagement: 7.5, earnings: 1200000, services: 18, rating: 4.8, status: 'active', platforms: ['instagram', 'tiktok'] },
  { id: 3, name: 'Sandra Adje', email: 'sandra.a@gmail.com', country: 'Bénin', tier: 'silver', followers: 89000, engagement: 6.8, earnings: 450000, services: 8, rating: 4.7, status: 'active', platforms: ['instagram'] },
  { id: 4, name: 'Yaovi Komla', email: 'yaovi.k@gmail.com', country: 'Togo', tier: 'silver', followers: 67000, engagement: 5.4, earnings: 280000, services: 5, rating: 4.5, status: 'active', platforms: ['tiktok', 'youtube'] },
  { id: 5, name: 'Fatou Bello', email: 'fatou.b@gmail.com', country: 'Bénin', tier: 'bronze', followers: 34000, engagement: 4.2, earnings: 120000, services: 3, rating: 4.3, status: 'active', platforms: ['instagram'] },
  { id: 6, name: 'Kofi Mensah', email: 'kofi.m@gmail.com', country: 'Ghana', tier: 'bronze', followers: 21000, engagement: 3.8, earnings: 85000, services: 2, rating: 4.1, status: 'inactive', platforms: ['facebook'] },
]

const tierConfig = {
  gold: { label: 'Gold', variant: 'warning', color: 'text-amber-600', bg: 'bg-amber-50' },
  silver: { label: 'Silver', variant: 'neutral', color: 'text-slate-600', bg: 'bg-slate-100' },
  bronze: { label: 'Bronze', variant: 'neutral', color: 'text-coral-600', bg: 'bg-coral-500/10' },
}

const platformIcons = {
  instagram: Camera,
  youtube: Video,
  facebook: Share2,
  tiktok: Music,
}

export default function Creators() {
  const [search, setSearch] = useState('')
  const [filterTier, setFilterTier] = useState('all')

  const filtered = mockCreators.filter(c => {
    if (filterTier !== 'all' && c.tier !== filterTier) return false
    if (search && !c.name.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  return (
    <div className="space-y-6">
      <PageHeader
        title="Créateurs de contenu"
        description="Classement par engagement, services UGC et revenus générés"
        icon={Sparkles}
        actions={<button className="btn-secondary"><Download className="w-4 h-4" />Export</button>}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Créateurs actifs" value={mockCreators.filter(c => c.status === 'active').length} icon={Sparkles} color="mantota" />
        <StatCard label="Revenus générés" value="3.02M FCFA" icon={DollarSign} color="purple" trend="up" trendValue="+24%" />
        <StatCard label="Services UGC" value="48" icon={Star} color="blue" />
        <StatCard label="Engagement moyen" value="6.0%" icon={TrendingUp} color="coral" />
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input type="text" placeholder="Rechercher un créateur..." value={search} onChange={e => setSearch(e.target.value)} className="input pl-9" />
          </div>
          <div className="flex items-center gap-1">
            {['all', 'gold', 'silver', 'bronze'].map(t => (
              <button key={t} onClick={() => setFilterTier(t)}
                className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize',
                  filterTier === t ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                )}>
                {t === 'all' ? 'Tous' : t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Creator cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((c, i) => {
          const tier = tierConfig[c.tier]
          return (
            <div key={c.id} className="card card-hover p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-400 to-coral-500 flex items-center justify-center text-white font-bold">
                    {c.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-slate-900">{c.name}</p>
                      {i < 3 && <Award className="w-4 h-4 text-amber-500" />}
                    </div>
                    <p className="text-xs text-slate-400">{c.country}</p>
                  </div>
                </div>
                <Badge variant={tier.variant}>{tier.label}</Badge>
              </div>

              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="p-2 rounded-lg bg-slate-50 text-center">
                  <Users className="w-3.5 h-3.5 text-slate-400 mx-auto mb-1" />
                  <p className="text-sm font-bold text-slate-900">{c.followers >= 1000 ? `${(c.followers / 1000).toFixed(0)}k` : c.followers}</p>
                  <p className="text-[10px] text-slate-400">followers</p>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 text-center">
                  <TrendingUp className="w-3.5 h-3.5 text-slate-400 mx-auto mb-1" />
                  <p className="text-sm font-bold text-slate-900">{c.engagement}%</p>
                  <p className="text-[10px] text-slate-400">engagement</p>
                </div>
                <div className="p-2 rounded-lg bg-slate-50 text-center">
                  <Star className="w-3.5 h-3.5 text-slate-400 mx-auto mb-1" />
                  <p className="text-sm font-bold text-slate-900">{c.rating}</p>
                  <p className="text-[10px] text-slate-400">note</p>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-slate-50">
                <div>
                  <p className="text-xs text-slate-400">Revenus générés</p>
                  <p className="text-sm font-bold text-mantota-600">{c.earnings.toLocaleString()} FCFA</p>
                </div>
                <div className="flex items-center gap-1.5">
                  {c.platforms.map(p => {
                    const Icon = platformIcons[p]
                    return Icon ? <Icon key={p} className="w-4 h-4 text-slate-400" /> : null
                  })}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
