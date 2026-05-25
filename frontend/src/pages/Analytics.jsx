import { useState, useEffect } from 'react'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts'
import Navbar from '../components/Navbar'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

const PRIORITY_COLORS = {
  Low: '#a0aec0',
  Medium: '#4299e1',
  High: '#dd6b20',
  Critical: '#e53e3e',
}

const PIE_COLORS = ['#4299e1', '#48bb78', '#ed8936', '#9f7aea', '#38b2ac',
                    '#ed64a6', '#f56565', '#ecc94b', '#667eea', '#fc8181']

export default function Analytics() {
  const { user } = useAuth()
  const [overview, setOverview] = useState(null)
  const [categories, setCategories] = useState([])
  const [sla, setSla] = useState([])
  const [agents, setAgents] = useState([])
  const [trends, setTrends] = useState([])
  const [etlRuns, setEtlRuns] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user || (user.role !== 'Admin' && user.role !== 'Supervisor')) {
      setLoading(false)
      return
    }
    Promise.all([
      api.get('/api/analytics/overview'),
      api.get('/api/analytics/categories'),
      api.get('/api/analytics/sla'),
      api.get('/api/analytics/agents'),
      api.get('/api/analytics/trends'),
      api.get('/api/analytics/etl-runs?limit=5'),
    ])
      .then(([o, c, s, a, t, e]) => {
        setOverview(o.data)
        setCategories(c.data)
        setSla(s.data)
        setAgents(a.data)
        setTrends(t.data)
        setEtlRuns(e.data)
      })
      .catch((err) => {
        const detail = err.response?.data?.detail
        if (typeof detail === 'string' && detail.toLowerCase().includes('run the etl')) {
          setError('No analytics data yet. Run the ETL pipeline first: python -m backend.etl.run_etl')
        } else {
          setError(detail || 'Failed to load analytics')
        }
      })
      .finally(() => setLoading(false))
  }, [user])

  if (!user) return null
  if (user.role !== 'Admin' && user.role !== 'Supervisor') {
    return (
      <>
        <Navbar />
        <div className="container">
          <div className="alert alert-error">
            Analytics is restricted to Admin and Supervisor roles.
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <Navbar />
      <div className="container">
        <h2 className="page-title">Analytics Dashboard</h2>
        <p style={{ color: '#718096', marginBottom: 24 }}>
          Powered by the Phase 2 ETL pipeline. Data refreshes when the ETL runs.
        </p>

        {loading && <div className="loading">Loading analytics...</div>}
        {error && <div className="alert alert-error">{error}</div>}

        {!loading && !error && overview && (
          <>
            {/* Top KPI cards */}
            <div className="stats-grid">
              <StatCard label="Total Complaints (Analytics)" value={overview.total_complaints.toLocaleString()} />
              <StatCard label="Resolved" value={overview.resolved_count.toLocaleString()} variant="success" />
              <StatCard label="Open / Pending" value={overview.open_count.toLocaleString()} variant="warning" />
              <StatCard label="SLA Breaches" value={overview.sla_breach_count.toLocaleString()} variant="danger" />
              <StatCard label="SLA Breach Rate" value={`${overview.sla_breach_rate_pct}%`} variant="danger" />
              <StatCard label="Avg Resolution (hrs)" value={overview.avg_resolution_hours ?? '—'} />
              <StatCard label="Avg Feedback Rating" value={overview.avg_feedback_rating ?? '—'} />
              <StatCard
                label="Last ETL Run"
                value={overview.last_etl_run ? new Date(overview.last_etl_run).toLocaleString() : 'Never'}
              />
            </div>

            {/* Monthly trends */}
            <div className="card">
              <h3 style={{ marginBottom: 16 }}>Monthly Complaint Trends</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year_month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="total_complaints" stroke="#4299e1" name="Total" strokeWidth={2} />
                  <Line type="monotone" dataKey="resolved_count" stroke="#48bb78" name="Resolved" strokeWidth={2} />
                  <Line type="monotone" dataKey="sla_breach_count" stroke="#e53e3e" name="SLA Breaches" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Category breakdown */}
            <div className="card">
              <h3 style={{ marginBottom: 16 }}>Complaints by Category</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={categories} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="category" type="category" width={150} fontSize={11} />
                    <Tooltip />
                    <Bar dataKey="total_complaints" fill="#4299e1" name="Total" />
                  </BarChart>
                </ResponsiveContainer>
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={categories}
                      dataKey="total_complaints"
                      nameKey="category"
                      cx="50%" cy="50%" outerRadius={110} label
                    >
                      {categories.map((_, i) => (
                        <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* SLA breach heatmap-style table */}
            <div className="card">
              <h3 style={{ marginBottom: 16 }}>SLA Breach Rate by Priority & Category</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Priority</th>
                      <th>Category</th>
                      <th>Total</th>
                      <th>Breached</th>
                      <th>Breach Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sla.slice(0, 15).map((row, i) => (
                      <tr key={i} style={{ cursor: 'default' }}>
                        <td>
                          <span className="badge" style={{
                            background: PRIORITY_COLORS[row.priority] || '#cbd5e0',
                            color: 'white',
                          }}>{row.priority}</span>
                        </td>
                        <td>{row.category}</td>
                        <td>{row.total_complaints}</td>
                        <td>{row.breached_count}</td>
                        <td>
                          <strong style={{
                            color: row.breach_rate_pct > 30 ? '#c53030' :
                                   row.breach_rate_pct > 20 ? '#dd6b20' : '#2f855a',
                          }}>
                            {row.breach_rate_pct}%
                          </strong>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Agent performance */}
            <div className="card">
              <h3 style={{ marginBottom: 16 }}>Agent Performance</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Handled</th>
                      <th>Resolved</th>
                      <th>Resolution Rate</th>
                      <th>Avg Resolution (hrs)</th>
                      <th>SLA Breach Rate</th>
                      <th>Avg Rating</th>
                    </tr>
                  </thead>
                  <tbody>
                    {agents.map((a) => (
                      <tr key={a.agent_id} style={{ cursor: 'default' }}>
                        <td><strong>{a.agent_id}</strong></td>
                        <td>{a.total_handled}</td>
                        <td>{a.resolved_count}</td>
                        <td>
                          <strong style={{ color: a.resolution_rate_pct >= 75 ? '#2f855a' : '#dd6b20' }}>
                            {a.resolution_rate_pct}%
                          </strong>
                        </td>
                        <td>{a.avg_resolution_hours ?? '—'}</td>
                        <td>{a.breach_rate_pct}%</td>
                        <td>{a.avg_feedback_rating ? `${a.avg_feedback_rating} ★` : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* ETL runs audit */}
            <div className="card">
              <h3 style={{ marginBottom: 16 }}>Recent ETL Runs</h3>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Run ID</th>
                      <th>Status</th>
                      <th>Source File</th>
                      <th>Extracted</th>
                      <th>Loaded</th>
                      <th>Finished At</th>
                    </tr>
                  </thead>
                  <tbody>
                    {etlRuns.map((r) => (
                      <tr key={r.run_id} style={{ cursor: 'default' }}>
                        <td>#{r.run_id}</td>
                        <td>
                          <span className="badge" style={{
                            background: r.status === 'SUCCESS' ? '#48bb78' : '#e53e3e',
                            color: 'white',
                          }}>{r.status}</span>
                        </td>
                        <td>{r.source_file}</td>
                        <td>{r.rows_extracted?.toLocaleString()}</td>
                        <td>{r.rows_loaded?.toLocaleString()}</td>
                        <td>{r.finished_at ? new Date(r.finished_at).toLocaleString() : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
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
      <div className="stat-value" style={{ fontSize: '1.6rem' }}>{value}</div>
    </div>
  )
}
