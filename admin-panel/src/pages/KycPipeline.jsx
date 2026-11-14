import { useState } from 'react'
import {
  ShieldCheck, CheckCircle2, XCircle, Clock, Search, Download,
  UserCircle, CreditCard, MapPin, Calendar, AlertTriangle, Eye,
  ChevronDown, FileText, TrendingUp,
} from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'

const mockKycSubmissions = [
  {
    id: 'KYC-001', user: 'Komi Agbodjan', email: 'komi.a@gmail.com', phone: '+228 90 12 34 56',
    country: 'Togo', city: 'Lomé', id_type: 'CNI', id_number: 'TG-12345678',
    id_expiry: '2028-05-15', submitted_at: '26 Aoû 2026', status: 'pending',
    risk_score: 15, shop_name: 'TechStore Lomé', plan: 'starter',
    doc_front: true, doc_back: true, selfie: true,
  },
  {
    id: 'KYC-002', user: 'Mariam Sow', email: 'mariam.s@gmail.com', phone: '+229 01 95 44 55 66',
    country: 'Bénin', city: 'Cotonou', id_type: 'Passeport', id_number: 'BJ-P789456',
    id_expiry: '2027-12-01', submitted_at: '25 Aoû 2026', status: 'pending',
    risk_score: 8, shop_name: 'Cotonou Fashion', plan: 'starter',
    doc_front: true, doc_back: true, selfie: true,
  },
  {
    id: 'KYC-003', user: 'Sani Boubacar', email: 'sani.b@gmail.com', phone: '+227 90 12 34 56',
    country: 'Niger', city: 'Niamey', id_type: 'CNI', id_number: 'NE-456789',
    id_expiry: '2026-09-30', submitted_at: '24 Aoû 2026', status: 'pending',
    risk_score: 45, shop_name: 'Niamey Shop', plan: 'starter',
    doc_front: true, doc_back: false, selfie: true,
  },
  {
    id: 'KYC-004', user: 'Issa Baraze', email: 'issa.b@gmail.com', phone: '+229 01 94 77 88 99',
    country: 'Bénin', city: 'Parakou', id_type: 'CNI', id_number: 'BJ-987654',
    id_expiry: '2025-03-01', submitted_at: '20 Aoû 2026', status: 'pending',
    risk_score: 72, shop_name: 'Parakou Deals', plan: 'free',
    doc_front: true, doc_back: true, selfie: false,
  },
  {
    id: 'KYC-005', user: 'Ibrahim Touré', email: 'ibrahim.t@gmail.com', phone: '+223 76 12 34 56',
    country: 'Mali', city: 'Bamako', id_type: 'CNI', id_number: 'ML-321654',
    id_expiry: '2026-11-15', submitted_at: '18 Aoû 2026', status: 'rejected',
    risk_score: 88, shop_name: 'Bamako Deals', plan: 'free',
    doc_front: true, doc_back: true, selfie: true,
  },
  {
    id: 'KYC-006', user: 'Koffi Adebayo', email: 'koffi@gmail.com', phone: '+229 01 97 12 34 56',
    country: 'Bénin', city: 'Porto-Novo', id_type: 'Passeport', id_number: 'BJ-P123456',
    id_expiry: '2029-06-20', submitted_at: '15 Aoû 2026', status: 'verified',
    risk_score: 5, shop_name: 'Boutique Elite', plan: 'pro',
    doc_front: true, doc_back: true, selfie: true,
  },
]

const riskConfig = {
  low: { label: 'Faible', color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-100' },
  medium: { label: 'Moyen', color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100' },
  high: { label: 'Élevé', color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-100' },
}

function getRiskLevel(score) {
  if (score < 30) return 'low'
  if (score < 60) return 'medium'
  return 'high'
}

export default function KycPipeline() {
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('pending')
  const [selectedKyc, setSelectedKyc] = useState(null)

  const filtered = mockKycSubmissions.filter(k => {
    if (filterStatus !== 'all' && k.status !== filterStatus) return false
    if (search) {
      const q = search.toLowerCase()
      if (!k.user.toLowerCase().includes(q) && !k.email.toLowerCase().includes(q) && !k.id.toLowerCase().includes(q)) return false
    }
    return true
  })

  const stats = {
    pending: mockKycSubmissions.filter(k => k.status === 'pending').length,
    verified: mockKycSubmissions.filter(k => k.status === 'verified').length,
    rejected: mockKycSubmissions.filter(k => k.status === 'rejected').length,
    avgTime: '4.2h',
  }

  if (selectedKyc) {
    return <KycDetail kyc={selectedKyc} onBack={() => setSelectedKyc(null)} />
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="KYC Pipeline"
        description="Validation visuelle des pièces d'identité des vendeurs et créateurs"
        icon={ShieldCheck}
        badge={<Badge variant="warning">{stats.pending} en attente</Badge>}
        actions={
          <button className="btn-secondary">
            <Download className="w-4 h-4" />
            Export
          </button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="En attente" value={stats.pending} icon={Clock} color="amber" />
        <StatCard label="Vérifiés" value={stats.verified} icon={CheckCircle2} color="mantota" />
        <StatCard label="Rejetés" value={stats.rejected} icon={XCircle} color="red" />
        <StatCard label="Temps moyen" value={stats.avgTime} icon={TrendingUp} color="blue" />
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input type="text" placeholder="Rechercher user, email, ID KYC..." value={search} onChange={e => setSearch(e.target.value)} className="input pl-9" />
          </div>
          <div className="flex items-center bg-slate-100 rounded-lg p-1">
            {['pending', 'verified', 'rejected', 'all'].map(s => (
              <button
                key={s}
                onClick={() => setFilterStatus(s)}
                className={clsx('px-3 py-1.5 rounded-md text-xs font-medium transition-colors',
                  filterStatus === s ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500'
                )}
              >
                {s === 'all' ? 'Tous' : s === 'pending' ? 'En attente' : s === 'verified' ? 'Vérifiés' : 'Rejetés'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* KYC Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map(kyc => {
          const risk = getRiskLevel(kyc.risk_score)
          const riskCfg = riskConfig[risk]
          return (
            <div key={kyc.id} className="card card-hover p-5 cursor-pointer" onClick={() => setSelectedKyc(kyc)}>
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-xl bg-slate-100 flex items-center justify-center">
                    <UserCircle className="w-6 h-6 text-slate-400" />
                  </div>
                  <div>
                    <p className="font-semibold text-slate-900 text-sm">{kyc.user}</p>
                    <p className="text-xs text-slate-400">{kyc.email}</p>
                  </div>
                </div>
                <Badge variant={kyc.status === 'verified' ? 'success' : kyc.status === 'pending' ? 'warning' : 'danger'}>
                  {kyc.status === 'verified' ? 'Vérifié' : kyc.status === 'pending' ? 'En attente' : 'Rejeté'}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                <div className="flex items-center gap-1.5 text-slate-500">
                  <MapPin className="w-3.5 h-3.5" />
                  {kyc.country}
                </div>
                <div className="flex items-center gap-1.5 text-slate-500">
                  <CreditCard className="w-3.5 h-3.5" />
                  {kyc.id_type}
                </div>
                <div className="flex items-center gap-1.5 text-slate-500">
                  <FileText className="w-3.5 h-3.5" />
                  {kyc.shop_name}
                </div>
                <div className="flex items-center gap-1.5 text-slate-500">
                  <Calendar className="w-3.5 h-3.5" />
                  {kyc.submitted_at}
                </div>
              </div>

              {/* Documents status */}
              <div className="flex items-center gap-2 mb-3">
                {kyc.doc_front && <Badge variant="success"><CheckCircle2 className="w-3 h-3" />Recto</Badge>}
                {kyc.doc_back && <Badge variant="success"><CheckCircle2 className="w-3 h-3" />Verso</Badge>}
                {kyc.selfie && <Badge variant="success"><CheckCircle2 className="w-3 h-3" />Selfie</Badge>}
                {!kyc.doc_back && <Badge variant="danger"><XCircle className="w-3 h-3" />Verso manquant</Badge>}
                {!kyc.selfie && <Badge variant="danger"><XCircle className="w-3 h-3" />Selfie manquant</Badge>}
              </div>

              {/* Risk score */}
              <div className={clsx('p-3 rounded-lg border', riskCfg.bg, riskCfg.border)}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-slate-600">Score de risque</span>
                  <span className={clsx('text-sm font-bold', riskCfg.color)}>{kyc.risk_score}/100</span>
                </div>
                <div className="w-full h-1.5 rounded-full bg-white/50 overflow-hidden">
                  <div className={clsx('h-full rounded-full',
                    risk === 'low' ? 'bg-green-500' : risk === 'medium' ? 'bg-amber-500' : 'bg-red-500'
                  )} style={{ width: `${kyc.risk_score}%` }}></div>
                </div>
                <div className="flex items-center justify-between mt-1.5">
                  <span className={clsx('text-xs font-semibold', riskCfg.color)}>{riskCfg.label}</span>
                  {kyc.id_expiry < new Date().toISOString().split('T')[0] && (
                    <span className="text-xs text-red-500 font-medium flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />Pièce expirée
                    </span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function KycDetail({ kyc, onBack }) {
  const risk = getRiskLevel(kyc.risk_score)
  const riskCfg = riskConfig[risk]

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <div className="flex items-center gap-4">
        <button onClick={onBack} className="btn-ghost p-2 rounded-lg">
          <ChevronDown className="w-5 h-5 rotate-90" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-slate-900">{kyc.user}</h1>
            <Badge variant={kyc.status === 'verified' ? 'success' : kyc.status === 'pending' ? 'warning' : 'danger'}>
              {kyc.status === 'verified' ? 'Vérifié' : kyc.status === 'pending' ? 'En attente' : 'Rejeté'}
            </Badge>
          </div>
          <p className="text-sm text-slate-500 mt-0.5 font-mono">{kyc.id} · Soumis le {kyc.submitted_at}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Documents */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Documents d'identité</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <DocPreview label="Pièce (recto)" present={kyc.doc_front} />
              <DocPreview label="Pièce (verso)" present={kyc.doc_back} />
              <DocPreview label="Selfie" present={kyc.selfie} />
            </div>
          </div>

          <div className="card p-6">
            <h3 className="font-semibold text-slate-900 mb-4">Informations</h3>
            <div className="grid grid-cols-2 gap-4">
              <InfoBox icon={UserCircle} label="Nom complet" value={kyc.user} />
              <InfoBox icon={MapPin} label="Localisation" value={`${kyc.city}, ${kyc.country}`} />
              <InfoBox icon={CreditCard} label="Type de pièce" value={kyc.id_type} />
              <InfoBox icon={FileText} label="Numéro de pièce" value={kyc.id_number} mono />
              <InfoBox icon={Calendar} label="Expiration" value={kyc.id_expiry} danger={kyc.id_expiry < new Date().toISOString().split('T')[0]} />
              <InfoBox icon={FileText} label="Boutique" value={kyc.shop_name} />
            </div>
          </div>
        </div>

        {/* Actions sidebar */}
        <div className="space-y-4">
          <div className={clsx('card p-5 border-2', riskCfg.border)}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-slate-900">Évaluation</h3>
              <Badge variant={risk === 'low' ? 'success' : risk === 'medium' ? 'warning' : 'danger'}>
                {riskCfg.label}
              </Badge>
            </div>
            <div className="text-center mb-3">
              <p className={clsx('text-4xl font-bold', riskCfg.color)}>{kyc.risk_score}</p>
              <p className="text-xs text-slate-400">Score de risque / 100</p>
            </div>
            <div className="space-y-2 text-xs">
              <RiskFactor label="Pièce valide" positive={!kyc.id_expiry || kyc.id_expiry >= new Date().toISOString().split('T')[0]} />
              <RiskFactor label="Tous documents présents" positive={kyc.doc_front && kyc.doc_back && kyc.selfie} />
              <RiskFactor label="Compte récent" positive={false} />
              <RiskFactor label="Pays à risque" positive={kyc.country === 'Niger' || kyc.country === 'Mali' ? false : true} />
            </div>
          </div>

          {kyc.status === 'pending' && (
            <div className="card p-5">
              <h3 className="font-semibold text-slate-900 mb-4">Actions</h3>
              <div className="space-y-3">
                <button className="btn-primary w-full">
                  <CheckCircle2 className="w-4 h-4" />
                  Approuver le KYC
                </button>
                <button className="btn-danger w-full">
                  <XCircle className="w-4 h-4" />
                  Rejeter le KYC
                </button>
                <button className="btn-secondary w-full">
                  <AlertTriangle className="w-4 h-4" />
                  Demander plus de documents
                </button>
              </div>
            </div>
          )}

          <div className="card p-5">
            <h3 className="font-semibold text-slate-900 mb-3">Historique</h3>
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2 text-slate-500">
                <Clock className="w-3 h-3" />
                <span>KYC soumis le {kyc.submitted_at}</span>
              </div>
              {kyc.status === 'verified' && (
                <div className="flex items-center gap-2 text-green-600">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Approuvé par Admin</span>
                </div>
              )}
              {kyc.status === 'rejected' && (
                <div className="flex items-center gap-2 text-red-500">
                  <XCircle className="w-3 h-3" />
                  <span>Rejeté — Documents insuffisants</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function DocPreview({ label, present }) {
  return (
    <div>
      <p className="text-xs text-slate-400 mb-2">{label}</p>
      <div className={clsx('aspect-[4/3] rounded-xl border-2 flex items-center justify-center transition-colors',
        present ? 'border-slate-200 bg-slate-50 hover:border-mantota-300 cursor-pointer' : 'border-dashed border-red-200 bg-red-50/30'
      )}>
        {present ? (
          <Eye className="w-8 h-8 text-slate-300" />
        ) : (
          <div className="text-center">
            <XCircle className="w-8 h-8 text-red-300 mx-auto mb-1" />
            <p className="text-xs text-red-400">Manquant</p>
          </div>
        )}
      </div>
    </div>
  )
}

function InfoBox({ icon: Icon, label, value, mono, danger }) {
  return (
    <div className="p-3 rounded-lg bg-slate-50">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className="w-3.5 h-3.5 text-slate-400" />
        <span className="text-xs text-slate-400">{label}</span>
      </div>
      <p className={clsx('text-sm font-medium', mono && 'font-mono', danger ? 'text-red-600' : 'text-slate-900')}>{value}</p>
    </div>
  )
}

function RiskFactor({ label, positive }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-500">{label}</span>
      {positive ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500" /> : <XCircle className="w-3.5 h-3.5 text-red-400" />}
    </div>
  )
}
