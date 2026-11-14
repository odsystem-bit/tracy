import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import {
  LayoutDashboard, Activity, TrendingUp, DollarSign, Globe2,
  Users, Sparkles, Store, ShieldCheck,
  ShoppingBag, Truck, Scale, Bot, Settings2, ScrollText,
  ShieldAlert, Bell, Zap, Wallet,
  Cog, HeartPulse, ChevronLeft, LogOut,
  Lightbulb,
} from 'lucide-react'

const navSections = [
  {
    title: 'Pilotage',
    items: [
      { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/operations', icon: Activity, label: 'Centre d\'opérations' },
    ],
  },
  {
    title: 'Business',
    items: [
      { to: '/growth', icon: TrendingUp, label: 'Croissance & Rétention' },
      { to: '/revenue', icon: DollarSign, label: 'Revenus & Commissions' },
      { to: '/countries', icon: Globe2, label: 'Performance par pays' },
    ],
  },
  {
    title: 'Communauté',
    items: [
      { to: '/users', icon: Users, label: 'Utilisateurs' },
      { to: '/creators', icon: Sparkles, label: 'Créateurs' },
    ],
  },
  {
    title: 'Boutiques',
    items: [
      { to: '/shops-map', icon: Store, label: 'Carte des boutiques' },
      { to: '/shop-quality', icon: ShieldCheck, label: 'Qualité boutiques' },
    ],
  },
  {
    title: 'Finance',
    items: [
      { to: '/cashflow', icon: DollarSign, label: 'Cockpit financier' },
      { to: '/payouts', icon: Wallet, label: 'Payouts' },
      { to: '/fraud', icon: ShieldAlert, label: 'Fraude & anomalies' },
    ],
  },
  {
    title: 'Commandes',
    items: [
      { to: '/orders', icon: ShoppingBag, label: 'Commandes live' },
      { to: '/delivery', icon: Truck, label: 'Performance livraison' },
      { to: '/disputes', icon: Scale, label: 'Litiges' },
    ],
  },
  {
    title: 'Tracy Core',
    items: [
      { to: '/tracy-status', icon: Bot, label: 'Pilotage Tracy' },
      { to: '/tracy-config', icon: Settings2, label: 'Configuration IA' },
      { to: '/tracy-logs', icon: ScrollText, label: 'Logs & analytics' },
      { to: '/knowledge-gaps', icon: Lightbulb, label: 'Lacunes RAG' },
    ],
  },
  {
    title: 'Trust & Safety',
    items: [
      { to: '/security', icon: ShieldAlert, label: 'Sécurité' },
    ],
  },
  {
    title: 'Communications',
    items: [
      { to: '/campaigns', icon: Zap, label: 'Campagnes' },
      { to: '/push-notifs', icon: Bell, label: 'Notifications' },
    ],
  },
  {
    title: 'Système',
    items: [
      { to: '/settings', icon: Cog, label: 'Réglages' },
      { to: '/system-health', icon: HeartPulse, label: 'Santé système' },
    ],
  },
]

export default function Sidebar({ collapsed, onToggleCollapse }) {
  return (
    <aside className={clsx(
      'fixed left-0 top-0 bottom-0 bg-sidebar flex flex-col z-40 transition-all duration-300 sidebar-scroll overflow-y-auto',
      collapsed ? 'w-16' : 'w-64'
    )}>
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-slate-800/50 shrink-0">
        <img src="/mantota-logo.png" alt="MANTOTA" className={clsx('shrink-0 transition-all', collapsed ? 'h-7' : 'h-9')} />
        {!collapsed && (
          <div className="flex-1 min-w-0">
            <p className="text-white font-bold text-sm truncate">MANTOTA</p>
            <p className="text-slate-500 text-[10px] truncate">Admin Panel</p>
          </div>
        )}
        <button
          onClick={onToggleCollapse}
          className="text-slate-500 hover:text-white transition-colors shrink-0"
        >
          <ChevronLeft className={clsx('w-4 h-4 transition-transform', collapsed && 'rotate-180')} />
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-3 space-y-1">
        {navSections.map((section) => (
          <div key={section.title} className="mb-2">
            {!collapsed && <p className="sidebar-section">{section.title}</p>}
            {collapsed && <div className="h-px bg-slate-800/50 my-2 mx-2" />}
            {section.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => clsx('sidebar-link', isActive && 'sidebar-link-active')}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className="w-4.5 h-4.5 shrink-0" style={{ width: 18, height: 18 }} />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-2 py-3 border-t border-slate-800/50 shrink-0">
        <NavLink to="/login" className="sidebar-link text-red-400 hover:text-red-300 hover:bg-red-500/10">
          <LogOut className="w-4.5 h-4.5 shrink-0" style={{ width: 18, height: 18 }} />
          {!collapsed && <span>Déconnexion</span>}
        </NavLink>
      </div>
    </aside>
  )
}

