import { useState, useMemo } from 'react'
import { ChevronLeft, ChevronRight, ArrowUpDown, Search } from 'lucide-react'
import clsx from 'clsx'

export default function DataTable({ columns, data, loading, pagination, onPageChange, searchable, searchKeys }) {
  const [search, setSearch] = useState('')
  const [sortKey, setSortKey] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  const filteredData = useMemo(() => {
    if (!search) return data
    const lower = search.toLowerCase()
    return data.filter(row =>
      (searchKeys || columns.map(c => c.key)).some(key =>
        String(row[key] ?? '').toLowerCase().includes(lower)
      )
    )
  }, [data, search, searchKeys, columns])

  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData
    return [...filteredData].sort((a, b) => {
      const aVal = a[sortKey]
      const bVal = b[sortKey]
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir === 'asc' ? aVal - bVal : bVal - aVal
      }
      return sortDir === 'asc'
        ? String(aVal ?? '').localeCompare(String(bVal ?? ''))
        : String(bVal ?? '').localeCompare(String(aVal ?? ''))
    })
  }, [filteredData, sortKey, sortDir])

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  return (
    <div className="card overflow-hidden">
      {searchable && (
        <div className="p-4 border-b border-slate-100">
          <div className="relative max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Rechercher..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="input pl-9 py-2"
            />
          </div>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr>
              {columns.map(col => (
                <th
                  key={col.key}
                  className={clsx('table-header', col.sortable !== false && 'cursor-pointer select-none hover:bg-slate-100')}
                  onClick={() => col.sortable !== false && handleSort(col.key)}
                  style={col.width ? { width: col.width } : {}}
                >
                  <div className="flex items-center gap-1.5">
                    {col.label}
                    {col.sortable !== false && (
                      <ArrowUpDown className={clsx('w-3 h-3', sortKey === col.key ? 'text-mantota-500' : 'text-slate-300')} />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {columns.map(col => (
                    <td key={col.key} className="table-cell">
                      <div className="h-4 bg-slate-100 rounded animate-pulse"></div>
                    </td>
                  ))}
                </tr>
              ))
            ) : sortedData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="table-cell text-center text-slate-400 py-12">
                  Aucune donnée
                </td>
              </tr>
            ) : (
              sortedData.map((row, i) => (
                <tr key={row.id || i} className="table-row transition-colors">
                  {columns.map(col => (
                    <td key={col.key} className="table-cell">
                      {col.render ? col.render(row) : row[col.key]}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {pagination && pagination.last_page > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100">
          <p className="text-xs text-slate-500">
            Affichage {pagination.from}–{pagination.to} sur {pagination.total}
          </p>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange(pagination.current_page - 1)}
              disabled={pagination.current_page === 1}
              className="btn-ghost p-1.5 rounded-lg disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            {Array.from({ length: Math.min(pagination.last_page, 7) }).map((_, i) => {
              let page = i + 1
              if (pagination.last_page > 7) {
                if (pagination.current_page > 4) {
                  page = pagination.current_page - 3 + i
                }
                if (pagination.current_page > pagination.last_page - 3) {
                  page = pagination.last_page - 6 + i
                }
              }
              if (page < 1 || page > pagination.last_page) return null
              return (
                <button
                  key={page}
                  onClick={() => onPageChange(page)}
                  className={clsx(
                    'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                    page === pagination.current_page
                      ? 'bg-mantota-500 text-white'
                      : 'text-slate-600 hover:bg-slate-100'
                  )}
                >
                  {page}
                </button>
              )
            })}
            <button
              onClick={() => onPageChange(pagination.current_page + 1)}
              disabled={pagination.current_page === pagination.last_page}
              className="btn-ghost p-1.5 rounded-lg disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
