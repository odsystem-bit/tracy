import { useState } from 'react'
import clsx from 'clsx'
import Sidebar from './Sidebar'
import Topbar from './Topbar'

export default function Layout({ children }) {
  const [collapsed, setCollapsed] = useState(false)

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar collapsed={collapsed} onToggleCollapse={() => setCollapsed(!collapsed)} />
      <div className={clsx('transition-all duration-300', collapsed ? 'ml-16' : 'ml-64')}>
        <Topbar onToggleSidebar={() => setCollapsed(!collapsed)} />
        <main className="p-6 animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  )
}
