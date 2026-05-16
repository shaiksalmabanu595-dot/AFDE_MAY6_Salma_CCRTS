import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { dashboardAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    dashboardAPI.stats()
      .then(({ data }) => setStats(data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load stats'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      <Navbar />
      <div className="container">
        <h2 className="page-title">Dashboard</h2>
        <p style={{ color: '#718096', marginBottom: 24 }}>
          Welcome back, <strong>{user?.name}</strong>. Here's your complaint overview.
        </p>

        {loading && <div className="loading">Loading stats...</div>}
        {error && <div className="alert alert-error">{error}</div>}

        {stats && (
          <>
            <div className="stats-grid">
              <StatCard label="Total Complaints" value={stats.total} />
              <StatCard label="Open" value={stats.open} variant="warning" />
              <StatCard label="In Progress" value={stats.in_progress} />
              <StatCard label="Resolved" value={stats.resolved} variant="success" />
              <StatCard label="Closed" value={stats.closed} />
              <StatCard label="SLA Breached" value={stats.sla_breached} variant="danger" />
              <StatCard label="Escalated" value={stats.escalated} variant="danger" />
              <StatCard
                label="Avg Resolution (hrs)"
                value={stats.avg_resolution_hours ?? 0}
              />
            </div>

            <div className="card">
              <h3 style={{ marginBottom: 16, color: '#2d3748' }}>By Priority</h3>
              <BreakdownBars data={stats.by_priority} colors={{
                Low: '#a0aec0', Medium: '#4299e1', High: '#dd6b20', Critical: '#e53e3e',
              }} />
            </div>

            <div className="card">
              <h3 style={{ marginBottom: 16, color: '#2d3748' }}>By Category</h3>
              {Object.keys(stats.by_category).length === 0 ? (
                <div className="empty-state">No complaints yet</div>
              ) : (
                <BreakdownBars data={stats.by_category} defaultColor="#4299e1" />
              )}
            </div>
          </>
        )}
      </div>
    </>
  )
}

function StatCard({ label, value, variant }) {
  return (
    <div className={`stat-card ${variant || ''}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
    </div>
  )
}

function BreakdownBars({ data, colors = {}, defaultColor = '#4299e1' }) {
  const max = Math.max(...Object.values(data), 1)
  return (
    <div>
      {Object.entries(data).map(([key, val]) => (
        <div key={key} style={{ marginBottom: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', marginBottom: 4 }}>
            <span style={{ fontWeight: 500 }}>{key}</span>
            <span style={{ color: '#718096' }}>{val}</span>
          </div>
          <div style={{ background: '#edf2f7', borderRadius: 4, height: 10, overflow: 'hidden' }}>
            <div
              style={{
                width: `${(val / max) * 100}%`,
                background: colors[key] || defaultColor,
                height: '100%',
                transition: 'width 0.3s',
              }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}
