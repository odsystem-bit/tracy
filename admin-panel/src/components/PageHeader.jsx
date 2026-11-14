import clsx from 'clsx'

export default function PageHeader({ title, description, icon: Icon, actions, badge }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div className="flex items-start gap-3">
        {Icon && (
          <div className="w-10 h-10 rounded-xl bg-mantota-50 flex items-center justify-center shrink-0">
            <Icon className="w-5 h-5 text-mantota-600" />
          </div>
        )}
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
            {badge}
          </div>
          <p className="text-sm text-slate-500 mt-0.5">{description}</p>
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
