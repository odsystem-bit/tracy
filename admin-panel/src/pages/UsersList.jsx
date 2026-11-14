import { useState, useMemo, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Users, Search, Filter, Download, Ban, Unlock, Wallet, Mail,
  Eye, MoreVertical, ChevronDown, UserCircle, MapPin, Phone,
  ShoppingBag, Package, ShieldCheck, TrendingUp, Calendar,
  CheckCircle2, XCircle, Clock, ArrowLeft, CreditCard, Sparkles, Store,
} from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import DataTable from '../components/DataTable'
import { adminApi } from '../api/admin'
import clsx from 'clsx'


const roleConfig = {
  vendor: { label: 'Vendeur', color: 'info', icon: Package },
  influencer: { label: 'Créateur', color: 'warning', icon: Sparkles },
  buyer: { label: 'Acheteur', color: 'neutral', icon: ShoppingBag },
  admin: { label: 'Admin', color: 'danger', icon: ShieldCheck },
}

const kycConfig = {
  verified: { label: 'Vérifié', variant: 'success', icon: CheckCircle2 },
  pending: { label: 'En attente', variant: 'warning', icon: Clock },
  rejected: { label: 'Rejeté', variant: 'danger', icon: XCircle },
  none: { label: 'Aucun', variant: 'neutral', icon: UserCircle },
}

const planConfig = {
  pro: { label: 'Pro', color: 'bg-purple-100 text-purple-700' },
  standard: { label: 'Standard', color: 'bg-blue-100 text-blue-700' },
  starter: { label: 'Starter', color: 'bg-mantota-100 text-mantota-700' },
  free: { label: 'Free', color: 'bg-slate-100 text-slate-600' },
}

export default function UsersList() {
  const navigate = useNavigate()
  const [selectedUser, setSelectedUser] = useState(null)
  const [filterRole, setFilterRole] = useState('all')
  const [filterKyc, setFilterKyc] = useState('all')
  const [filterCountry, setFilterCountry] = useState('all')
  const [search, setSearch] = useState('')
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    const params = { per_page: 50 }
    if (filterRole !== 'all') params.role = filterRole
    if (search) params.search = search
    if (filterKyc === 'banned') params.status = 'banned'

    setLoading(true)
    adminApi.getUsers(params)
      .then(res => {
        setUsers(res.data.data || [])
        setTotal(res.data.meta?.total ?? 0)
        setLoading(false)
      })
      .catch(() => {
        setUsers([])
        setTotal(0)
        setLoading(false)
      })
  }, [filterRole, filterKyc, search])

  const filtered = useMemo(() => {
    return users.filter(u => {
      if (filterCountry !== 'all' && u.country !== filterCountry) return false
      if (filterKyc !== 'all' && filterKyc !== 'banned' && u.kyc_status !== filterKyc) return false
      return true
    })
  }, [users, filterKyc, filterCountry])

  const countries = [...new Set(users.map(u => u.country).filter(Boolean))]

  const stats = {
    total: total || users.length,
    vendors: users.filter(u => u.role === 'vendor').length,
    creators: users.filter(u => u.role === 'influencer').length,
    buyers: users.filter(u => u.role === 'buyer').length,
  }

  const handleToggleBan = async (id) => {
    try {
      await adminApi.toggleBan(id)
      setUsers(prev => prev.map(u => u.id === id ? { ...u, is_banned: !u.is_banned } : u))
    } catch (e) {
      console.error('Ban failed:', e)
    }
  }

  if (selectedUser) {
    return <UserDetail userId={selectedUser.id} fallbackUser={selectedUser} onBack={() => setSelectedUser(null)} onToggleBan={handleToggleBan} />
  }

  const columns = [
    {
      key: 'name',
      label: 'Utilisateur',
      render: (row) => (
        <div className="flex items-center gap-3">
          <div className={clsx('w-9 h-9 rounded-full flex items-center justify-center text-white font-semibold text-xs shrink-0',
            row.role === 'vendor' ? 'bg-blue-500' : row.role === 'influencer' ? 'bg-amber-500' : 'bg-slate-400'
          )}>
            {row.name.split(' ').map(n => n[0]).join('').toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="font-medium text-slate-900 truncate">{row.name}</p>
            <p className="text-xs text-slate-400 truncate">{row.email}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'role',
      label: 'Rôle',
      render: (row) => {
        const cfg = roleConfig[row.role]
        return <Badge variant={cfg.color}>{cfg.label}</Badge>
      },
    },
    {
      key: 'country',
      label: 'Pays',
      render: (row) => (
        <span className="flex items-center gap-1.5 text-sm text-slate-600">
          <MapPin className="w-3.5 h-3.5 text-slate-400" />
          {row.country}
        </span>
      ),
    },
    {
      key: 'kyc_status',
      label: 'KYC',
      render: (row) => {
        const cfg = kycConfig[row.kyc_status]
        return <Badge variant={cfg.variant}><cfg.icon className="w-3 h-3" />{cfg.label}</Badge>
      },
    },
    {
      key: 'bot_plan',
      label: 'Plan',
      render: (row) => row.bot_plan ? (
        <span className={clsx('badge', planConfig[row.bot_plan]?.color || planConfig.free.color)}>{planConfig[row.bot_plan]?.label || 'Free'}</span>
      ) : <span className="text-slate-300 text-xs">—</span>,
    },
    {
      key: 'wallet_balance',
      label: 'Wallet',
      render: (row) => (
        <span className="font-semibold text-slate-700">{Number(row.wallet_balance).toLocaleString()} <span className="text-xs text-slate-400">FCFA</span></span>
      ),
    },
    {
      key: 'created_at',
      label: 'Inscrit le',
      render: (row) => <span className="text-sm text-slate-500">{new Date(row.created_at).toLocaleDateString('fr-FR')}</span>,
    },
    {
      key: 'actions',
      label: '',
      sortable: false,
      render: (row) => (
        <div className="flex items-center gap-1">
          <button onClick={() => setSelectedUser(row)} className="btn-ghost p-1.5 rounded-lg hover:bg-mantota-50 hover:text-mantota-600" title="Voir détails">
            <Eye className="w-4 h-4" />
          </button>
          <button className="btn-ghost p-1.5 rounded-lg" title="Actions">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Utilisateurs"
        description="Gestion unifiée de tous les utilisateurs de la plateforme"
        icon={Users}
        badge={<Badge variant="info">{stats.total} total</Badge>}
        actions={
          <>
            <button className="btn-secondary">
              <Download className="w-4 h-4" />
              Export
            </button>
            <button className="btn-primary">
              <Mail className="w-4 h-4" />
              Email groupé
            </button>
          </>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total utilisateurs" value={stats.total.toLocaleString()} icon={Users} color="mantota" />
        <StatCard label="Vendeurs" value={stats.vendors} icon={Package} color="blue" />
        <StatCard label="Créateurs" value={stats.creators} icon={Sparkles} color="amber" />
        <StatCard label="Acheteurs" value={stats.buyers} icon={ShoppingBag} color="coral" />
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Rechercher par nom, email, téléphone..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-9"
            />
          </div>
          <FilterSelect label="Rôle" value={filterRole} onChange={setFilterRole} options={[
            { value: 'all', label: 'Tous les rôles' },
            { value: 'vendor', label: 'Vendeurs' },
            { value: 'influencer', label: 'Créateurs' },
            { value: 'buyer', label: 'Acheteurs' },
          ]} />
          <FilterSelect label="KYC" value={filterKyc} onChange={setFilterKyc} options={[
            { value: 'all', label: 'Tous KYC' },
            { value: 'verified', label: 'Vérifiés' },
            { value: 'pending', label: 'En attente' },
            { value: 'rejected', label: 'Rejetés' },
            { value: 'none', label: 'Aucun' },
          ]} />
          <FilterSelect label="Pays" value={filterCountry} onChange={setFilterCountry} options={[
            { value: 'all', label: 'Tous les pays' },
            ...countries.map(c => ({ value: c, label: c })),
          ]} />
        </div>
      </div>

      {/* Table */}
      <DataTable columns={columns} data={filtered} />

      <p className="text-xs text-slate-400 text-center">{filtered.length} utilisateur(s) affiché(s)</p>
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

function UserDetail({ userId, fallbackUser, onBack, onToggleBan }) {
  const [activeTab, setActiveTab] = useState('profile')
  const [user, setUser] = useState(fallbackUser || null)
  const [loading, setLoading] = useState(!fallbackUser)

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    adminApi.getUser(userId)
      .then(res => {
        setUser(res.data)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [userId])

  const tabs = [
    { id: 'profile', label: 'Profil', icon: UserCircle },
    { id: 'wallet', label: 'Wallet', icon: Wallet },
    { id: 'orders', label: 'Commandes', icon: ShoppingBag },
    { id: 'shop', label: 'Boutique', icon: Package },
    { id: 'kyc', label: 'KYC', icon: ShieldCheck },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-3 border-mantota-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="text-center py-16">
        <p className="text-sm text-slate-400">Utilisateur introuvable</p>
        <button onClick={onBack} className="btn-secondary mt-4">Retour</button>
      </div>
    )
  }

  const safeName = user.name || '—'
  const initials = safeName.split(' ').map(n => n[0]).join('').toUpperCase()

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="btn-ghost p-2 rounded-lg">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-4 flex-1">
          <div className={clsx('w-14 h-14 rounded-2xl flex items-center justify-center text-white font-bold text-lg shrink-0',
            user.role === 'vendor' ? 'bg-blue-500' : user.role === 'influencer' ? 'bg-amber-500' : 'bg-slate-400'
          )}>
            {initials}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2.5">
              <h1 className="text-2xl font-bold text-slate-900">{safeName}</h1>
              <Badge variant={roleConfig[user.role]?.color || 'neutral'}>{roleConfig[user.role]?.label || user.role}</Badge>
              {user.is_banned && <Badge variant="danger"><Ban className="w-3 h-3" />Banni</Badge>}
            </div>
            <p className="text-sm text-slate-500 mt-0.5">{user.email || '—'} · {user.phone || '—'} · {user.country || '—'}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!user.is_banned ? (
            <button className="btn-danger" onClick={() => onToggleBan(user.id)}>
              <Ban className="w-4 h-4" />
              Bannir
            </button>
          ) : (
            <button className="btn-secondary" onClick={() => onToggleBan(user.id)}>
              <Unlock className="w-4 h-4" />
              Débloquer
            </button>
          )}
          <button className="btn-secondary">
            <Mail className="w-4 h-4" />
            Email
          </button>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="Wallet" value={`${Number(user.wallet_balance || 0).toLocaleString()} FCFA`} icon={Wallet} color="mantota" />
        <StatCard label="Commandes" value={user.order_count || 0} icon={ShoppingBag} color="blue" />
        <StatCard label="Produits" value={user.product_count || 0} icon={Package} color="coral" />
        <StatCard label="Revenus générés" value={`${Number(user.revenue || 0).toLocaleString()} FCFA`} icon={TrendingUp} color="purple" />
        <StatCard label="Inscrit le" value={user.created_at ? new Date(user.created_at).toLocaleDateString('fr-FR') : '—'} icon={Calendar} color="amber" />
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === tab.id
                ? 'text-mantota-600 border-mantota-500'
                : 'text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-50'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="animate-fade-in">
        {activeTab === 'profile' && <ProfileTab user={user} />}
        {activeTab === 'wallet' && <WalletTab user={user} />}
        {activeTab === 'orders' && <OrdersTab user={user} />}
        {activeTab === 'shop' && <ShopTab user={user} />}
        {activeTab === 'kyc' && <KycTab user={user} />}
      </div>
    </div>
  )
}

function ProfileTab({ user }) {
  const fields = [
    { label: 'Nom complet', value: user.name || '—', icon: UserCircle },
    { label: 'Email', value: user.email || '—', icon: Mail },
    { label: 'Téléphone', value: user.phone || '—', icon: Phone },
    { label: 'Pays', value: user.country || '—', icon: MapPin },
    { label: 'Rôle principal', value: roleConfig[user.role]?.label || user.role, icon: ShieldCheck },
    { label: 'Date d\'inscription', value: user.created_at ? new Date(user.created_at).toLocaleDateString('fr-FR', { year: 'numeric', month: 'long', day: 'numeric' }) : '—', icon: Calendar },
  ]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Informations personnelles</h3>
        <div className="space-y-4">
          {fields.map(f => (
            <div key={f.label} className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                <f.icon className="w-4 h-4 text-slate-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-400">{f.label}</p>
                <p className="text-sm font-medium text-slate-900 truncate">{f.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Modes activés</h3>
        <div className="space-y-3">
          {['buyer', 'vendor', 'partner', 'influencer'].map(mode => {
            const isActive = (user.modes || []).includes(mode)
            const labels = { buyer: 'Acheteur', vendor: 'Vendeur', partner: 'Partenaire', influencer: 'Créateur' }
            return (
              <div key={mode} className="flex items-center justify-between p-3 rounded-lg border border-slate-100">
                <span className="text-sm font-medium text-slate-700">{labels[mode]}</span>
                <button className={clsx(
                  'relative w-11 h-6 rounded-full transition-colors',
                  isActive ? 'bg-mantota-500' : 'bg-slate-200'
                )}>
                  <span className={clsx(
                    'absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform',
                    isActive ? 'translate-x-5' : 'translate-x-0.5'
                  )} />
                </button>
              </div>
            )
          })}
        </div>
        <div className="mt-4 p-3 rounded-lg bg-blue-50 border border-blue-100">
          <p className="text-xs text-blue-600">Les modes peuvent être activés/désactivés. L'utilisateur garde un seul compte pour tous ses modes.</p>
        </div>
      </div>
    </div>
  )
}

function WalletTab({ user }) {
  const balance = Number(user.wallet_balance || 0)
  const balances = [
    { label: 'Balance disponible', value: balance, color: 'text-mantota-600', bg: 'bg-mantota-50' },
  ]

  const transactions = user.recent_transactions || []

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {balances.map(b => (
          <div key={b.label} className="card p-5">
            <div className={clsx('w-10 h-10 rounded-lg flex items-center justify-center mb-3', b.bg)}>
              <Wallet className={clsx('w-5 h-5', b.color)} />
            </div>
            <p className="stat-label">{b.label}</p>
            <p className="stat-value mt-1">{b.value.toLocaleString()} <span className="text-sm text-slate-400">FCFA</span></p>
          </div>
        ))}
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Transactions récentes</h3>
        {transactions.length === 0 ? (
          <div className="text-center py-8 text-sm text-slate-400">Aucune transaction récente</div>
        ) : (
          <div className="space-y-2">
            {transactions.map((tx, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg hover:bg-slate-50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center',
                    tx.type === 'deposit' || tx.type === 'earning' ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-500'
                  )}>
                    <TrendingUp className={clsx('w-4 h-4', tx.type !== 'deposit' && tx.type !== 'earning' && 'rotate-180')} />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">{tx.type} — {tx.reference || tx.id}</p>
                    <p className="text-xs text-slate-400">{tx.created_at ? new Date(tx.created_at).toLocaleDateString('fr-FR') : '—'}</p>
                  </div>
                </div>
                <span className={clsx('font-semibold text-sm', tx.type === 'deposit' || tx.type === 'earning' ? 'text-green-600' : 'text-red-500')}>
                  {tx.type === 'deposit' || tx.type === 'earning' ? '+' : ''}{Number(tx.amount).toLocaleString()} FCFA
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Actions wallet</h3>
        <div className="flex flex-wrap gap-3">
          <button className="btn-primary">
            <CreditCard className="w-4 h-4" />
            Créditer le wallet
          </button>
          <button className="btn-secondary">
            <Wallet className="w-4 h-4" />
            Locker le wallet
          </button>
        </div>
      </div>
    </div>
  )
}

function OrdersTab({ user }) {
  const orders = user.recent_orders || []
  return (
    <div className="card p-6">
      <h3 className="font-semibold text-slate-900 mb-4">Historique des commandes</h3>
      {orders.length === 0 ? (
        <div className="text-center py-12">
          <ShoppingBag className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-400">Aucune commande</p>
        </div>
      ) : (
        <div className="space-y-2">
          {orders.map((o, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
                  <ShoppingBag className="w-4 h-4 text-blue-500" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-900">{o.reference || o.id}</p>
                  <p className="text-xs text-slate-400">{o.product} · {o.created_at ? new Date(o.created_at).toLocaleDateString('fr-FR') : '—'}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="neutral">{o.status}</Badge>
                <span className="font-semibold text-sm text-slate-700">{Number(o.total).toLocaleString()} FCFA</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ShopTab({ user }) {
  if (!user.shop_name) {
    return (
      <div className="card p-12 text-center">
        <Package className="w-12 h-12 text-slate-300 mx-auto mb-3" />
        <p className="text-sm text-slate-400">Cet utilisateur n'a pas de boutique</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 card p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-mantota-400 to-mantota-600 flex items-center justify-center">
            <Store className="w-8 h-8 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 text-lg">{user.shop_name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="info">{planConfig[user.bot_plan]?.label || 'Free'}</Badge>
              <Badge variant={kycConfig[user.kyc_status].variant}>KYC {kycConfig[user.kyc_status].label}</Badge>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-slate-50">
            <p className="stat-label">Produits</p>
            <p className="text-xl font-bold text-slate-900 mt-1">{user.product_count}</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50">
            <p className="stat-label">Commandes totales</p>
            <p className="text-xl font-bold text-slate-900 mt-1">{user.order_count}</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50">
            <p className="stat-label">Revenus générés</p>
            <p className="text-xl font-bold text-slate-900 mt-1">{user.revenue.toLocaleString()} FCFA</p>
          </div>
          <div className="p-4 rounded-lg bg-slate-50">
            <p className="stat-label">Panier moyen</p>
            <p className="text-xl font-bold text-slate-900 mt-1">{user.order_count > 0 ? Math.round(user.revenue / user.order_count).toLocaleString() : 0} FCFA</p>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Localisation</h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <MapPin className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-700">{user.country}</span>
          </div>
          <div className="flex items-center gap-3">
            <Phone className="w-4 h-4 text-slate-400" />
            <span className="text-sm text-slate-700">{user.phone}</span>
          </div>
        </div>
        <div className="mt-4 h-48 rounded-lg bg-slate-100 flex items-center justify-center">
          <MapPin className="w-8 h-8 text-slate-300" />
        </div>
      </div>
    </div>
  )
}

function KycTab({ user }) {
  const cfg = kycConfig[user.kyc_status]

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-900">Statut KYC</h3>
          <Badge variant={cfg.variant}><cfg.icon className="w-3 h-3" />{cfg.label}</Badge>
        </div>
        <div className="space-y-3">
          <div className="p-4 rounded-lg border border-slate-100">
            <p className="text-xs text-slate-400 mb-2">Pièce d'identité (recto)</p>
            <div className="h-32 rounded-lg bg-slate-100 flex items-center justify-center">
              <CreditCard className="w-8 h-8 text-slate-300" />
            </div>
          </div>
          <div className="p-4 rounded-lg border border-slate-100">
            <p className="text-xs text-slate-400 mb-2">Pièce d'identité (verso)</p>
            <div className="h-32 rounded-lg bg-slate-100 flex items-center justify-center">
              <CreditCard className="w-8 h-8 text-slate-300" />
            </div>
          </div>
          <div className="p-4 rounded-lg border border-slate-100">
            <p className="text-xs text-slate-400 mb-2">Selfie</p>
            <div className="h-32 rounded-lg bg-slate-100 flex items-center justify-center">
              <UserCircle className="w-8 h-8 text-slate-300" />
            </div>
          </div>
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Actions KYC</h3>
        <div className="space-y-3">
          {user.kyc_status === 'pending' && (
            <>
              <button className="btn-primary w-full">
                <CheckCircle2 className="w-4 h-4" />
                Approuver le KYC
              </button>
              <button className="btn-danger w-full">
                <XCircle className="w-4 h-4" />
                Rejeter le KYC
              </button>
            </>
          )}
          {user.kyc_status === 'verified' && (
            <div className="p-4 rounded-lg bg-green-50 border border-green-100">
              <p className="text-sm text-green-600 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                KYC vérifié et approuvé
              </p>
            </div>
          )}
          {user.kyc_status === 'rejected' && (
            <div className="p-4 rounded-lg bg-red-50 border border-red-100">
              <p className="text-sm text-red-600 flex items-center gap-2">
                <XCircle className="w-4 h-4" />
                KYC rejeté
              </p>
            </div>
          )}
          {user.kyc_status === 'none' && (
            <div className="p-4 rounded-lg bg-slate-50 border border-slate-100">
              <p className="text-sm text-slate-500">Aucun KYC soumis par cet utilisateur</p>
            </div>
          )}
          <div className="pt-4 border-t border-slate-100">
            <h4 className="text-sm font-medium text-slate-700 mb-2">Historique</h4>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Clock className="w-3 h-3" />
                <span>KYC soumis le 20 Aoû 2026</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
