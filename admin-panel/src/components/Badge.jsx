import clsx from 'clsx'

const variants = {
  success: 'badge-success',
  warning: 'badge-warning',
  danger: 'badge-danger',
  info: 'badge-info',
  neutral: 'badge-neutral',
}

export default function Badge({ variant = 'neutral', children, className }) {
  return (
    <span className={clsx(variants[variant], className)}>
      {children}
    </span>
  )
}
