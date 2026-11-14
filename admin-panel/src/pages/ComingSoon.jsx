import { Construction } from 'lucide-react'

export default function ComingSoon({ title, description }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        <p className="text-sm text-slate-500 mt-0.5">{description}</p>
      </div>
      <div className="card p-12 flex flex-col items-center justify-center text-center">
        <div className="w-16 h-16 rounded-2xl bg-mantota-50 flex items-center justify-center mb-4">
          <Construction className="w-8 h-8 text-mantota-500" />
        </div>
        <h3 className="font-semibold text-slate-900 text-lg">En construction</h3>
        <p className="text-sm text-slate-400 mt-1 max-w-md">
          Cette page fait partie du panel admin MANTOTA. Elle sera développée selon le cahier des charges.
        </p>
        <div className="mt-6 px-4 py-2 rounded-lg bg-slate-50 border border-slate-100">
          <p className="text-xs text-slate-500 font-mono">{title}</p>
        </div>
      </div>
    </div>
  )
}
