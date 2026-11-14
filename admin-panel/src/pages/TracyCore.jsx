import { useState, useEffect } from 'react'
import {
  Bot, Activity, MessageSquare, Zap,
  Settings2, ScrollText, CheckCircle2,
  AlertCircle, Cpu, Gauge,
} from 'lucide-react'
import {
  AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import { adminApi } from '../api/admin'
import clsx from 'clsx'


export default function TracyCore() {
  const [activeTab, setActiveTab] = useState('status')
  const [tracyStatus, setTracyStatus] = useState(null)

  useEffect(() => {
    adminApi.getTracyStatus()
      .then(res => setTracyStatus(res.data))
      .catch(() => setTracyStatus({ online: false, error: 'Impossible de contacter le serveur' }))
  }, [])

  const isOnline = tracyStatus?.online ?? false

  const tabs = [
    { id: 'status', label: 'Pilotage', icon: Bot },
    { id: 'config', label: 'Configuration IA', icon: Settings2 },
    { id: 'logs', label: 'Logs & Analytics', icon: ScrollText },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tracy Core"
        description="Pilotage de l'IA conversationnelle — santé, conversations, configuration et analytics"
        icon={Bot}
        badge={
          <Badge variant={isOnline ? 'success' : 'danger'}>
            <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}>{''}</span>
            {isOnline ? 'En ligne' : 'Hors ligne'}
          </Badge>
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
          </button>
        ))}
      </div>

      <div className="animate-fade-in">
        {activeTab === 'status' && <StatusTab tracyStatus={tracyStatus} />}
        {activeTab === 'config' && <ConfigTab />}
        {activeTab === 'logs' && <LogsTab />}
      </div>
    </div>
  )
}

function StatusTab({ tracyStatus }) {
  const isOnline = tracyStatus?.online ?? false

  return (
    <div className="space-y-6">
      {/* Health KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isOnline ? 'bg-green-50' : 'bg-red-50'}`}>
              <Cpu className={`w-5 h-5 ${isOnline ? 'text-green-600' : 'text-red-500'}`} />
            </div>
            <Badge variant={isOnline ? 'success' : 'danger'}>
              {isOnline ? 'Opérationnel' : 'Hors ligne'}
            </Badge>
          </div>
          <p className="stat-label">API Tracy Core</p>
          <p className="stat-value mt-1">{tracyStatus?.url || '—'}</p>
          <p className="text-xs text-slate-400 mt-1">{tracyStatus?.error || 'Connecté'}</p>
        </div>
        <StatCard label="Conversations actives" value="—" icon={MessageSquare} color="blue" />
        <StatCard label="Taux conversion" value="—" icon={Zap} color="mantota" />
        <StatCard label="Temps réponse moyen" value="—" icon={Gauge} color="amber" />
      </div>

      {/* Activity chart */}
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-slate-900">Activité Tracy par heure</h3>
            <p className="text-xs text-slate-400 mt-0.5">Conversations par canal (aujourd'hui)</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="warning">V2</Badge>
          </div>
        </div>
        <div className="text-center py-12 text-sm text-slate-400">
          Analytics temps réel — disponible dans la V2 avec Redis + streaming d'événements
        </div>
      </div>

      {/* Tool usage + WhatsApp connections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900">Outils Tracy utilisés (7j)</h3>
            <Badge variant="warning">V2</Badge>
          </div>
          <div className="text-center py-12 text-sm text-slate-400">
            Historique des appels d'outils — disponible dans la V2 avec table d'analytics
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-slate-900">Connexions WhatsApp</h3>
            <Badge variant="warning">V2</Badge>
          </div>
          <div className="text-center py-12 text-sm text-slate-400">
            Connecteur WhatsApp — en cours d'intégration dans la V2
          </div>
        </div>
      </div>
    </div>
  )
}

function ConfigTab() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    adminApi.getTracyConfig()
      .then(res => {
        setConfig(res.data)
        setLoading(false)
      })
      .catch(err => {
        setError(err.response?.data?.error || 'Impossible de charger la configuration')
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-10 h-10 border-3 border-mantota-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-6">
        <div className="text-center py-12">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-sm text-red-600 font-medium">{error}</p>
          <p className="text-xs text-slate-400 mt-1">Vérifiez que Tracy Core est en ligne</p>
        </div>
      </div>
    )
  }

  const configItems = [
    { label: 'Environnement', value: config.environment, icon: Cpu },
    { label: 'Port', value: config.port, icon: Activity },
    { label: 'Fournisseur IA', value: config.ai_provider, icon: Zap },
    { label: 'Fournisseur de repli', value: config.fallback_ai_provider || 'aucun', icon: AlertCircle },
    { label: 'Modèle OpenAI', value: config.openai_model, icon: Bot },
    { label: 'Modèle Ollama', value: config.ollama_model, icon: Bot },
    { label: 'URL Ollama', value: config.ollama_base_url, icon: Activity },
    { label: 'Forme d\'adresse', value: config.address_form === 'tu' ? 'Tutoiement' : 'Vouvoiement', icon: MessageSquare },
    { label: 'Température IA', value: config.ai_temperature, icon: Gauge },
    { label: 'Historique max conversation', value: config.max_conversation_history + ' messages', icon: MessageSquare },
    { label: 'Rate limit', value: config.rate_limit_per_minute + ' req/min', icon: Zap },
    { label: 'URL API Mantota', value: config.mantota_api_url, icon: Activity },
    { label: 'TTL mémoire courte', value: (config.short_term_memory_ttl / 60) + ' min', icon: Gauge },
  ]

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-slate-900">Configuration générale</h3>
            <p className="text-xs text-slate-400 mt-0.5">Paramètres actuels de Tracy Core (lecture seule)</p>
          </div>
          <Badge variant="info">{config.environment}</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {configItems.map((item, i) => (
            <div key={i} className="flex items-center gap-3 p-3 rounded-lg border border-slate-100">
              <div className="w-9 h-9 rounded-lg bg-slate-50 flex items-center justify-center shrink-0">
                <item.icon className="w-4 h-4 text-slate-500" />
              </div>
              <div className="min-w-0">
                <p className="text-xs text-slate-400">{item.label}</p>
                <p className="text-sm font-semibold text-slate-900 truncate">{String(item.value)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card p-6">
        <h3 className="font-semibold text-slate-900 mb-4">Outils enregistrés ({config.tools_registered?.length || 0})</h3>
        <div className="flex flex-wrap gap-2">
          {config.tools_registered?.map(tool => (
            <span key={tool} className="px-3 py-1.5 rounded-lg bg-slate-50 text-xs font-medium text-slate-600 border border-slate-100">
              {tool}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

function LogsTab() {
  const [filterLevel, setFilterLevel] = useState('all')
  const levelConfig = {
    info: { color: 'text-blue-600', bg: 'bg-blue-50', icon: Activity },
    success: { color: 'text-green-600', bg: 'bg-green-50', icon: CheckCircle2 },
    warning: { color: 'text-amber-600', bg: 'bg-amber-50', icon: AlertCircle },
    error: { color: 'text-red-600', bg: 'bg-red-50', icon: AlertCircle },
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Logs (24h)" value="—" icon={ScrollText} color="blue" />
        <StatCard label="Erreurs" value="—" icon={AlertCircle} color="red" />
        <StatCard label="Warnings" value="—" icon={AlertCircle} color="amber" />
        <StatCard label="Succès" value="—" icon={CheckCircle2} color="mantota" />
      </div>

      <div className="card p-4">
        <div className="flex items-center gap-2">
          {['all', 'info', 'success', 'warning', 'error'].map(l => (
            <button
              key={l}
              onClick={() => setFilterLevel(l)}
              className={clsx('px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize',
                filterLevel === l ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              )}
            >
              {l === 'all' ? 'Tous' : l}
            </button>
          ))}
        </div>
      </div>

      <div className="card p-6">
        <div className="text-center py-12 text-sm text-slate-400">
          Logs non disponibles — endpoint logs Tracy Core à développer
        </div>
      </div>
    </div>
  )
}
