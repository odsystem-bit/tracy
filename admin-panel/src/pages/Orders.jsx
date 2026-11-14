import { useState, useEffect, useMemo } from 'react'
import {
  ShoppingBag, Search, Download, Eye, ChevronDown, Filter,
  Package, Truck, Scale, Clock, CheckCircle2, XCircle, AlertTriangle,
  MapPin, DollarSign, User, Phone, ArrowLeft, MessageSquare,
  TrendingUp, Calendar, Store,
} from 'lucide-react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import { adminApi } from '../api/admin'
import clsx from 'clsx'

const statusConfig = {
  pending: { label: 'En attente', variant: 'warning', icon: Clock },
  paid: { label: 'Payée', variant: 'info', icon: CheckCircle2 },
  shipped: { label: 'Expédiée', variant: 'info', icon: Truck },
  delivered: { label: 'Livrée', variant: 'success', icon: CheckCircle2 },
  disputed: { label: 'Litige', variant: 'danger', icon: AlertTriangle },
  cancelled: { label: 'Annulée', variant: 'neutral', icon: XCircle },
  refunded: { label: 'Remboursée', variant: 'neutral', icon: DollarSign },
}


export default function Orders() {
  const [activeTab, setActiveTab] = useState('orders')
  const [selectedOrder, setSelectedOrder] = useState(null)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    const params = { per_page: 50 }
    if (filterStatus !== 'all') params.status = filterStatus
    if (search) params.search = search

    adminApi.getOrders(params)
      .then(res => {
        setOrders((res.data.data || []).map(o => ({
          ...o,
          id: o.order_number || String(o.id),
          ref: o.order_number || String(o.id),
          customer: o.customer || 'N/A',
          product: o.product || 'N/A',
          amount: o.total || 0,
          commission: o.commission || 0,
          vendor_earnings: o.vendor_earnings || 0,
          delivery_fee: o.delivery_fee || 0,
          delivery_company: o.delivery_company || 'N/A',
          vendor: o.vendor || 'N/A',
          country: o.country || 'N/A',
          city: o.city || 'N/A',
          tracking_token: o.tracking_token || 'N/A',
          status: o.status || 'pending',
          is_overdue: o.is_overdue || false,
          created_at: o.created_at ? new Date(o.created_at).toLocaleDateString('fr-FR') : '—',
        })))
      })
      .catch(() => setOrders([]))
      .finally(() => setLoading(false))
  }, [filterStatus, search])

  const tabs = [
    { id: 'orders', label: 'Commandes', icon: ShoppingBag, count: orders.length },
    { id: 'delivery', label: 'Livraison', icon: Truck },
    { id: 'disputes', label: 'Litiges', icon: Scale, count: orders.filter(o => o.status === 'disputed').length },
  ]

  const filtered = orders.filter(o => {
    if (filterStatus !== 'all' && o.status !== filterStatus) return false
    if (search) {
      const q = search.toLowerCase()
      if (!o.id.toLowerCase().includes(q) && !o.customer.toLowerCase().includes(q) && !o.vendor.toLowerCase().includes(q) && !o.product.toLowerCase().includes(q)) return false
    }
    return true
  })

  if (selectedOrder) {
    return <OrderDetail order={selectedOrder} onBack={() => setSelectedOrder(null)} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Commandes"
        description="Suivi des commandes en temps réel, performance livraison et résolution des litiges"
        icon={ShoppingBag}
        actions={
          <button className="btn-secondary">
            <Download className="w-4 h-4" />
            Export
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
            {tab.count !== undefined && (
              <span className={clsx('badge text-[10px]',
                tab.id === 'disputes' && tab.count > 0 ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'
              )}>{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-10 h-10 border-3 border-mantota-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : (
      <div className="animate-fade-in">
        {activeTab === 'orders' && (
          <OrdersTab
            orders={filtered}
            search={search}
            setSearch={setSearch}
            filterStatus={filterStatus}
            setFilterStatus={setFilterStatus}
            onSelectOrder={setSelectedOrder}
          />
        )}
        {activeTab === 'delivery' && <DeliveryTab orders={orders} />}
        {activeTab === 'disputes' && <DisputesTab orders={orders.filter(o => o.status === 'disputed')} onSelectOrder={setSelectedOrder} />}
      </div>
      )}
    </div>
  )
}

function OrdersTab({ orders, search, setSearch, filterStatus, setFilterStatus, onSelectOrder }) {
  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard label="Total commandes" value={orders.length} icon={ShoppingBag} color="mantota" />
        <StatCard label="Livrées" value={orders.filter(o => o.status === 'delivered').length} icon={CheckCircle2} color="blue" />
        <StatCard label="En transit" value={orders.filter(o => o.status === 'shipped' || o.status === 'paid').length} icon={Truck} color="amber" />
        <StatCard label="Litiges" value={orders.filter(o => o.status === 'disputed').length} icon={AlertTriangle} color="coral" />
        <StatCard label="En retard" value={orders.filter(o => o.is_overdue).length} icon={Clock} color="red" />
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input type="text" placeholder="Rechercher ID, client, vendeur, produit..." value={search} onChange={e => setSearch(e.target.value)} className="input pl-9" />
          </div>
          <div className="flex items-center gap-1 flex-wrap">
            {['all', 'pending', 'paid', 'shipped', 'delivered', 'disputed', 'cancelled'].map(s => (
              <button
                key={s}
                onClick={() => setFilterStatus(s)}
                className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  filterStatus === s ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                )}
              >
                {s === 'all' ? 'Toutes' : statusConfig[s]?.label || s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="table-header">Référence</th>
                <th className="table-header">Client</th>
                <th className="table-header">Vendeur</th>
                <th className="table-header">Produit</th>
                <th className="table-header">Montant</th>
                <th className="table-header">Livraison</th>
                <th className="table-header">Statut</th>
                <th className="table-header">Date</th>
                <th className="table-header"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {orders.map(o => {
                const cfg = statusConfig[o.status]
                return (
                  <tr key={o.id} className={clsx('table-row', o.is_overdue && 'bg-red-50/30')}>
                    <td className="table-cell">
                      <span className="font-mono text-xs font-medium text-slate-700">{o.id}</span>
                      {o.is_overdue && <span className="ml-2 text-[10px] text-red-500 font-semibold">EN RETARD</span>}
                    </td>
                    <td className="table-cell">
                      <p className="font-medium text-slate-900 text-sm">{o.customer}</p>
                      <p className="text-xs text-slate-400">{o.city}, {o.country}</p>
                    </td>
                    <td className="table-cell text-sm text-slate-600">{o.vendor}</td>
                    <td className="table-cell text-sm text-slate-600 max-w-[160px] truncate">{o.product}</td>
                    <td className="table-cell">
                      <span className="font-semibold text-slate-900">{o.amount.toLocaleString()}</span>
                      <span className="text-xs text-slate-400 ml-1">FCFA</span>
                    </td>
                    <td className="table-cell">
                      <span className="text-sm text-slate-600">{o.delivery_company}</span>
                    </td>
                    <td className="table-cell">
                      <Badge variant={cfg.variant}>
                        <cfg.icon className="w-3 h-3" />
                        {cfg.label}
                      </Badge>
                    </td>
                    <td className="table-cell text-sm text-slate-500">{o.created_at}</td>
                    <td className="table-cell">
                      <button onClick={() => onSelectOrder(o)} className="btn-ghost p-1.5 rounded-lg hover:bg-mantota-50 hover:text-mantota-600">
                        <Eye className="w-4 h-4" />
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

function DeliveryTab({ orders }) {
  const deliveryStats = useMemo(() => {
    const byCompany = {}
    orders.forEach(o => {
      const c = o.delivery_company || 'Inconnu'
      if (!byCompany[c]) byCompany[c] = { company: c, total: 0, onTime: 0, late: 0, failed: 0 }
      byCompany[c].total++
      if (o.status === 'delivered') byCompany[c].onTime++
      else if (o.is_overdue) byCompany[c].late++
      else if (o.status === 'cancelled') byCompany[c].failed++
    })
    return Object.values(byCompany)
  }, [orders])

  const totalDelivered = orders.filter(o => o.status === 'delivered').length
  const totalLate = orders.filter(o => o.is_overdue).length
  const totalFailed = orders.filter(o => o.status === 'cancelled').length
  const totalWithDelivery = orders.length || 1

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Taux à temps" value={`${Math.round((totalDelivered / totalWithDelivery) * 100)}%`} icon={CheckCircle2} color="mantota" />
        <StatCard label="Taux retard" value={`${Math.round((totalLate / totalWithDelivery) * 100)}%`} icon={Clock} color="amber" />
        <StatCard label="Taux échec" value={`${Math.round((totalFailed / totalWithDelivery) * 100)}%`} icon={XCircle} color="red" />
        <StatCard label="Total livraisons" value={orders.length} icon={Truck} color="blue" />
      </div>

      {deliveryStats.length === 0 ? (
        <div className="card p-8 text-center text-sm text-slate-400">Aucune donnée de livraison disponible</div>
      ) : (
        <>
          <div className="card p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Performance par service de livraison</h3>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={deliveryStats}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="company" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: '0.75rem', border: '1px solid #f1f5f9', fontSize: '12px' }} />
                <Legend wrapperStyle={{ fontSize: '12px' }} />
                <Bar dataKey="onTime" name="À temps" stackId="a" fill="#0BBFA0" radius={[0, 0, 0, 0]} />
                <Bar dataKey="late" name="En retard" stackId="a" fill="#F59E0B" radius={[0, 0, 0, 0]} />
                <Bar dataKey="failed" name="Échec" stackId="a" fill="#EF4444" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th className="table-header">Service</th>
                    <th className="table-header">Total</th>
                    <th className="table-header">À temps</th>
                    <th className="table-header">En retard</th>
                    <th className="table-header">Échecs</th>
                    <th className="table-header">Taux succès</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {deliveryStats.map(d => (
                    <tr key={d.company} className="table-row">
                      <td className="table-cell">
                        <div className="flex items-center gap-2">
                          <Truck className="w-4 h-4 text-slate-400" />
                          <span className="font-medium text-slate-900">{d.company}</span>
                        </div>
                      </td>
                      <td className="table-cell font-semibold text-slate-700">{d.total}</td>
                      <td className="table-cell text-green-600 font-medium">{d.onTime}</td>
                      <td className="table-cell text-amber-600 font-medium">{d.late}</td>
                      <td className="table-cell text-red-500 font-medium">{d.failed}</td>
                      <td className="table-cell">
                        <div className="flex items-center gap-2">
                          <div className="w-20 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                            <div className="h-full bg-mantota-500 rounded-full" style={{ width: `${d.total ? (d.onTime / d.total) * 100 : 0}%` }}></div>
                          </div>
                          <span className="text-xs font-medium text-slate-600">{d.total ? Math.round((d.onTime / d.total) * 100) : 0}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

function DisputesTab({ orders, onSelectOrder }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Litiges actifs" value={orders.length} icon={Scale} color="coral" />
        <StatCard label="Taux litige" value={orders.length > 0 ? `${Math.round((orders.length / orders.length) * 100)}%` : '0%'} icon={AlertTriangle} color="red" />
      </div>

      <div className="space-y-3">
        {orders.map(o => (
          <div key={o.id} className="card card-hover p-5 cursor-pointer" onClick={() => onSelectOrder(o)}>
            <div className="flex items-start gap-4">
              <div className="w-11 h-11 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
                <AlertTriangle className="w-5 h-5 text-red-500" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2.5 mb-1">
                  <p className="font-semibold text-slate-900 font-mono text-sm">{o.id}</p>
                  <Badge variant="danger">Litige ouvert</Badge>
                </div>
                <p className="text-sm text-slate-600">{o.product} — {o.amount.toLocaleString()} FCFA</p>
                <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                  <span>Client: <span className="font-medium text-slate-600">{o.customer}</span></span>
                  <span>Vendeur: <span className="font-medium text-slate-600">{o.vendor}</span></span>
                  <span>{o.created_at}</span>
                </div>
              </div>
              <button className="btn-secondary text-xs">
                <MessageSquare className="w-3.5 h-3.5" />
                Examiner
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function OrderDetail({ order, onBack }) {
  const [activeTab, setActiveTab] = useState('info')
  const cfg = statusConfig[order.status]

  const timeline = [
    { label: 'Commande créée', date: order.created_at, done: true, icon: ShoppingBag },
    { label: 'Paiement reçu', date: order.created_at, done: order.status !== 'pending' && order.status !== 'cancelled', icon: DollarSign },
    { label: 'Expédiée', date: order.status === 'shipped' || order.status === 'delivered' ? order.created_at : null, done: ['shipped', 'delivered'].includes(order.status), icon: Truck },
    { label: 'Livrée', date: order.status === 'delivered' ? order.created_at : null, done: order.status === 'delivered', icon: CheckCircle2 },
    { label: 'Escrow libéré', date: order.status === 'delivered' ? order.created_at : null, done: order.status === 'delivered', icon: CheckCircle2 },
  ]

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="btn-ghost p-2 rounded-lg">
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-slate-900 font-mono">{order.id}</h1>
            <Badge variant={cfg.variant}><cfg.icon className="w-3 h-3" />{cfg.label}</Badge>
            {order.is_overdue && <Badge variant="danger"><Clock className="w-3 h-3" />En retard</Badge>}
          </div>
          <p className="text-sm text-slate-500 mt-0.5">{order.product} · {order.created_at}</p>
        </div>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Montant total" value={`${order.amount.toLocaleString()} FCFA`} icon={DollarSign} color="mantota" />
        <StatCard label="Commission" value={`${order.commission.toLocaleString()} FCFA`} icon={TrendingUp} color="blue" />
        <StatCard label="Vendeur reçoit" value={`${order.vendor_earnings.toLocaleString()} FCFA`} icon={User} color="purple" />
        <StatCard label="Frais livraison" value={`${order.delivery_fee.toLocaleString()} FCFA`} icon={Truck} color="coral" />
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200">
        {[
          { id: 'info', label: 'Informations', icon: Package },
          { id: 'timeline', label: 'Timeline', icon: Clock },
          ...(order.status === 'disputed' ? [{ id: 'dispute', label: 'Litige', icon: Scale }] : []),
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={clsx(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors',
              activeTab === tab.id ? 'text-mantota-600 border-mantota-500' : 'text-slate-500 border-transparent hover:text-slate-700'
            )}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="animate-fade-in">
        {activeTab === 'info' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card p-6">
              <h3 className="font-semibold text-slate-900 mb-4">Client</h3>
              <div className="space-y-3">
                <InfoRow icon={User} label="Nom" value={order.customer} />
                <InfoRow icon={MapPin} label="Adresse" value={`${order.city}, ${order.country}`} />
                <InfoRow icon={Phone} label="Téléphone" value={order.customer_phone || 'N/A'} />
                <InfoRow icon={Package} label="Produit" value={order.product} />
              </div>
            </div>
            <div className="card p-6">
              <h3 className="font-semibold text-slate-900 mb-4">Vendeur & Livraison</h3>
              <div className="space-y-3">
                <InfoRow icon={Store} label="Boutique" value={order.vendor} />
                <InfoRow icon={Truck} label="Service" value={order.delivery_company} />
                <InfoRow icon={Package} label="Token suivi" value={order.tracking_token || 'N/A'} mono />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="card p-6">
            <h3 className="font-semibold text-slate-900 mb-6">Timeline de la commande</h3>
            <div className="space-y-1">
              {timeline.map((step, i) => (
                <div key={i} className="flex items-start gap-4">
                  <div className="flex flex-col items-center">
                    <div className={clsx('w-9 h-9 rounded-full flex items-center justify-center shrink-0',
                      step.done ? 'bg-mantota-100 text-mantota-600' : 'bg-slate-100 text-slate-300'
                    )}>
                      <step.icon className="w-4 h-4" />
                    </div>
                    {i < timeline.length - 1 && (
                      <div className={clsx('w-0.5 h-8', step.done ? 'bg-mantota-200' : 'bg-slate-100')}></div>
                    )}
                  </div>
                  <div className="pt-1.5">
                    <p className={clsx('text-sm font-medium', step.done ? 'text-slate-900' : 'text-slate-400')}>{step.label}</p>
                    {step.date && <p className="text-xs text-slate-400 mt-0.5">{step.date}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'dispute' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card p-6">
              <h3 className="font-semibold text-slate-900 mb-4">Chat du litige</h3>
              <div className="space-y-4 max-h-[400px] overflow-y-auto">
                <div className="text-center py-8 text-sm text-slate-400">
                  Messages de litige non disponibles via l'API actuelle.
                  <br />Raison du litige : {order.dispute_reason || 'Non spécifiée'}
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2">
                <input type="text" placeholder="Répondre en tant qu'admin..." className="input flex-1" />
                <button className="btn-primary">Envoyer</button>
              </div>
            </div>
            <div className="card p-6">
              <h3 className="font-semibold text-slate-900 mb-4">Résolution</h3>
              <div className="space-y-3">
                <button className="btn-danger w-full">
                  <DollarSign className="w-4 h-4" />
                  Rembourser client
                </button>
                <button className="btn-primary w-full">
                  <CheckCircle2 className="w-4 h-4" />
                  Favor vendeur
                </button>
                <button className="btn-secondary w-full">
                  <Scale className="w-4 h-4" />
                  Split (partiel)
                </button>
              </div>
              <div className="mt-4 pt-4 border-t border-slate-100">
                <p className="text-xs text-slate-400 mb-2">Montant en litige</p>
                <p className="text-2xl font-bold text-slate-900">{order.amount.toLocaleString()} <span className="text-sm text-slate-400">FCFA</span></p>
                <p className="text-xs text-slate-400 mt-1">Escrow bloqué jusqu'à résolution</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function InfoRow({ icon: Icon, label, value, mono }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
        <Icon className="w-4 h-4 text-slate-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-slate-400">{label}</p>
        <p className={clsx('text-sm font-medium text-slate-900 truncate', mono && 'font-mono')}>{value}</p>
      </div>
    </div>
  )
}
