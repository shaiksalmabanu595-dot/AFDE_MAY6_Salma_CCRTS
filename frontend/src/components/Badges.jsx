export function StatusBadge({ status }) {
  const cls = `badge badge-status-${status.replace(/\s/g, '')}`
  return <span className={cls}>{status}</span>
}

export function PriorityBadge({ priority }) {
  return <span className={`badge badge-priority-${priority}`}>{priority}</span>
}

export function SlaBadge({ breached }) {
  if (!breached) return null
  return <span className="badge badge-sla-breach">SLA BREACHED</span>
}
