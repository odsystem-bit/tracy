import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import UsersList from './pages/UsersList'
import ShopsMap from './pages/ShopsMap'
import Finance from './pages/Finance'
import Orders from './pages/Orders'
import KycPipeline from './pages/KycPipeline'
import TracyCore from './pages/TracyCore'
import Operations from './pages/Operations'
import Growth from './pages/Growth'
import Revenue from './pages/Revenue'
import Countries from './pages/Countries'
import Creators from './pages/Creators'
import Campaigns from './pages/Campaigns'
import Security from './pages/Security'
import Notifications from './pages/Notifications'
import System from './pages/System'
import ShopQuality from './pages/ShopQuality'
import Restaurants from './pages/Restaurants'
import KnowledgeGaps from './pages/KnowledgeGaps'
import ComingSoon from './pages/ComingSoon'

const realPages = [
  { path: '/users', component: UsersList },
  { path: '/shops-map', component: ShopsMap },
  { path: '/cashflow', component: Finance },
  { path: '/payouts', component: Finance },
  { path: '/fraud', component: Finance },
  { path: '/orders', component: Orders },
  { path: '/disputes', component: Orders },
  { path: '/delivery', component: Orders },
  { path: '/kyc', component: KycPipeline },
  { path: '/tracy-status', component: TracyCore },
  { path: '/tracy-config', component: TracyCore },
  { path: '/tracy-logs', component: TracyCore },
  { path: '/operations', component: Operations },
  { path: '/growth', component: Growth },
  { path: '/revenue', component: Revenue },
  { path: '/countries', component: Countries },
  { path: '/creators', component: Creators },
  { path: '/campaigns', component: Campaigns },
  { path: '/security', component: Security },
  { path: '/push-notifs', component: Notifications },
  { path: '/emails', component: Notifications },
  { path: '/announcements', component: Notifications },
  { path: '/settings', component: System },
  { path: '/audit-log', component: System },
  { path: '/system-health', component: System },
  { path: '/backup', component: System },
  { path: '/shop-quality', component: ShopQuality },
  { path: '/restaurants', component: Restaurants },
  { path: '/knowledge-gaps', component: KnowledgeGaps },
]

const comingSoonPages = [
  { path: '/geo-map', title: 'Carte géographique', desc: 'Heat map boutiques, users et commandes par zone' },
  { path: '/onboarding', title: 'Onboarding vendeurs', desc: 'Funnel visuel et relances' },
  { path: '/ambassadors', title: 'Ambassadeurs', desc: 'Programme de parrainage et performance' },
  { path: '/product-moderation', title: 'Modération produits', desc: 'File de validation et signalements' },
  { path: '/vendor-plans', title: 'Plans vendeurs', desc: 'Config plans freemium et abonnés' },
  { path: '/gateways', title: 'Passerelles & devises', desc: 'Config paiement et taux de change' },
  { path: '/service-orders', title: 'Commandes UGC', desc: 'Commandes de services créateurs' },
  { path: '/moderation', title: 'Modération communautaire', desc: 'Messages suspects et signalements' },
  { path: '/testimonials', title: 'Témoignages', desc: 'CRUD témoignages clients' },
  { path: '/partners', title: 'Partenaires', desc: 'CRUD partenaires' },
  { path: '/top-creators', title: 'Top créateurs', desc: 'Classement par earnings et engagement' },
  { path: '/top-vendors', title: 'Top vendeurs', desc: 'Classement par volume de ventes' },
  { path: '/visitors', title: 'Visiteurs', desc: 'Analytics trafic et heat map géo' },
]

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="*" element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/dashboard" element={<Dashboard />} />
                  {realPages.map(page => (
                    <Route key={page.path} path={page.path} element={<page.component />} />
                  ))}
                  {comingSoonPages.map(page => (
                    <Route
                      key={page.path}
                      path={page.path}
                      element={<ComingSoon title={page.title} description={page.desc} />}
                    />
                  ))}
                  <Route path="/" element={<Dashboard />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
