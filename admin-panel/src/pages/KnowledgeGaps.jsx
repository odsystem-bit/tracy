import { useState, useEffect } from 'react'
import { Lightbulb, AlertCircle, CheckCircle, Eye, TrendingUp, FileText } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Badge from '../components/Badge'
import clsx from 'clsx'
import { adminApi } from '../api/admin'

const STATUS_CONFIG = {
  open:      { label: 'Ouvert',     color: 'amber' },
  suggested: { label: 'Suggéré',    color: 'blue' },
  resolved:  { label: 'Résolu',     color: 'green' },
  ignored:   { label: 'Ignoré',     color: 'slate' },
}

export default function KnowledgeGaps() {
  const [gaps, setGaps] = useState([])
  const [loading, setLoading] = useState(true)
  const [statusFilter, setStatusFilter] = useState('')
  const [updating, setUpdating] = useState(null)

  useEffect(() => {
    fetchGaps()
  }, [statusFilter])

  const fetchGaps = () => {
    setLoading(true)
    const params = {}
    if (statusFilter) params.status = statusFilter
    adminApi.getKnowledgeGaps(params)
      .then(({ data }) => setGaps(data.data || []))
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  const updateGapStatus = (id, status, resolvedDocumentId = null) => {
    setUpdating(id)
    adminApi.updateKnowledgeGap(id, { status, resolved_document_id: resolvedDocumentId })
      .then(() => fetchGaps())
      .catch(() => {})
      .finally(() => setUpdating(null))
  }

  const suggestedCount = gaps.filter(g => g.status === 'suggested').length
  const openCount = gaps.filter(g => g.status === 'open').length
  const totalOccurrences = gaps.reduce((a, g) => a + (g.occurrence_count || 0), 0)

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lacunes de connaissance (RAG Correctif)"
        description="Requêtes sans réponse fiable — Tracy signale ce qu'elle ne sait pas"
        icon={Lightbulb}
      />

      {/* KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Lacunes suggérées" value={suggestedCount} icon={Lightbulb} color="blue" />
        <StatCard label="Lacunes ouvertes" value={openCount} icon={AlertCircle} color="coral" />
        <StatCard label="Occurrences totales" value={totalOccurrences} icon={TrendingUp} color="purple" />
        <StatCard label="Total lacunes" value={gaps.length} icon={FileText} color="mantota" />
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium text-slate-500 mr-2">Statut :</span>
          {['', 'suggested', 'open', 'resolved', 'ignored'].map(s => (
            <button
              key={s || 'all'}
              onClick={() => setStatusFilter(s)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                statusFilter === s ? 'bg-mantota-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              )}
            >
              {s === '' ? 'Tous' : STATUS_CONFIG[s]?.label || s}
            </button>
          ))}
        </div>
      </div>

      {/* Gaps table */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="w-8 h-8 border-2 border-mantota-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      ) : gaps.length === 0 ? (
        <div className="card p-12 text-center">
          <CheckCircle className="w-12 h-12 text-mantota-500 mx-auto mb-3" />
          <p className="text-slate-600 font-medium">Aucune lacune de connaissance</p>
          <p className="text-sm text-slate-400 mt-1">Tracy a trouvé une réponse fiable pour toutes les requêtes</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/50">
                  <th className="text-left px-4 py-3 font-medium text-slate-500 text-xs uppercase tracking-wider">Requête</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-500 text-xs uppercase tracking-wider">Catégorie</th>
                  <th className="text-center px-4 py-3 font-medium text-slate-500 text-xs uppercase tracking-wider">Occurrences</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-500 text-xs uppercase tracking-wider">Statut</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-500 text-xs uppercase tracking-wider">Dernière fois</th>
                  <th className="text-right px-4 py-3 font-medium text-slate-500 text-xs uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {gaps.map(gap => (
                  <tr key={gap.id} className="border-b border-slate-50 hover:bg-slate-50/30 transition-colors">
                    <td className="px-4 py-3 max-w-xs">
                      <p className="text-slate-900 font-medium truncate" title={gap.query_text}>
                        {gap.query_text}
                      </p>
                      {gap.country_id && (
                        <span className="text-xs text-slate-400">Pays #{gap.country_id}</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {gap.category_guess ? (
                        <span className="text-xs px-2 py-1 rounded-md bg-slate-100 text-slate-600">
                          {gap.category_guess}
                        </span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={clsx(
                        'inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold',
                        gap.occurrence_count >= 5 ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'
                      )}>
                        {gap.occurrence_count}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <Badge color={STATUS_CONFIG[gap.status]?.color || 'slate'}>
                        {STATUS_CONFIG[gap.status]?.label || gap.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">
                      {gap.last_seen_at ? new Date(gap.last_seen_at).toLocaleDateString('fr-FR') : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-1">
                        {gap.status !== 'ignored' && (
                          <button
                            onClick={() => updateGapStatus(gap.id, 'ignored')}
                            disabled={updating === gap.id}
                            className="p-1.5 rounded-lg text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors"
                            title="Ignorer"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                        {gap.status !== 'suggested' && (
                          <button
                            onClick={() => updateGapStatus(gap.id, 'suggested')}
                            disabled={updating === gap.id}
                            className="p-1.5 rounded-lg text-blue-400 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                            title="Marquer comme suggéré"
                          >
                            <Lightbulb className="w-4 h-4" />
                          </button>
                        )}
                        {gap.status !== 'resolved' && (
                          <button
                            onClick={() => updateGapStatus(gap.id, 'resolved')}
                            disabled={updating === gap.id}
                            className="p-1.5 rounded-lg text-green-400 hover:bg-green-50 hover:text-green-600 transition-colors"
                            title="Marquer comme résolu"
                          >
                            <CheckCircle className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Info banner */}
      <div className="card p-4 bg-blue-50/50 border-blue-100">
        <div className="flex items-start gap-3">
          <Lightbulb className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-slate-600">
            <p className="font-medium text-slate-700 mb-1">Comment ça marche</p>
            <p className="text-xs text-slate-500">
              Quand Tracy ne trouve pas d'information fiable (score de similarité trop bas), la requête est
              automatiquement enregistrée ici. Les lacunes qui reviennent souvent (≥ 5 occurrences) passent
              en « suggéré » — c'est un signal pour l'admin qu'un nouveau document de connaissance serait utile.
              Aucune création automatique : l'admin rédige et valide manuellement le document.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
