import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { StatusBadge, PriorityBadge, SlaBadge } from '../components/Badges'
import { complaintsAPI, categoriesAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'

const STATUSES = ['Open', 'Assigned', 'In Progress', 'Pending Customer Response', 'Escalated', 'Resolved', 'Closed']
const PRIORITIES = ['Low', 'Medium', 'High', 'Critical']

export default function ComplaintsList() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [complaints, setComplaints] = useState([])
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [filters, setFilters] = useState({
    search: '', status: '', priority: '', category_id: '',
    assigned_to_me: false, my_complaints: false,
  })

  useEffect(() => {
    categoriesAPI.list().then(({ data }) => setCategories(data)).catch(() => {})
  }, [])

  const loadComplaints = () => {
    setLoading(true)
    const params = {}
    Object.entries(filters).forEach(([k, v]) => {
      if (v !== '' && v !== false) params[k] = v
    })
    complaintsAPI.list(params)
      .then(({ data }) => setComplaints(data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadComplaints() }, [filters])

  const handleFilter = (key, value) => setFilters({ ...filters, [key]: value })
  const clearFilters = () => setFilters({
    search: '', status: '', priority: '', category_id: '',
    assigned_to_me: false, my_complaints: false,
  })

  return (
    <>
      <Navbar />
      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 className="page-title" style={{ marginBottom: 0 }}>Complaints</h2>
          {user?.role === 'Customer' && (
            <button className="btn btn-primary" onClick={() => navigate('/new-complaint')}>
              + New Complaint
            </button>
          )}
        </div>

        <div className="filters">
          <input
            placeholder="Search by title, description, or complaint code..."
            value={filters.search}
            onChange={(e) => handleFilter('search', e.target.value)}
          />
          <select value={filters.status} onChange={(e) => handleFilter('status', e.target.value)}>
            <option value="">All Statuses</option>
            {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <select value={filters.priority} onChange={(e) => handleFilter('priority', e.target.value)}>
            <option value="">All Priorities</option>
            {PRIORITIES.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <select value={filters.category_id} onChange={(e) => handleFilter('category_id', e.target.value)}>
            <option value="">All Categories</option>
            {categories.map(c => <option key={c.category_id} value={c.category_id}>{c.category_name}</option>)}
          </select>
          {user?.role === 'Agent' && (
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.9rem' }}>
              <input
                type="checkbox"
                checked={filters.assigned_to_me}
                onChange={(e) => handleFilter('assigned_to_me', e.target.checked)}
              />
              Assigned to me
            </label>
          )}
          <button className="btn btn-secondary btn-sm" onClick={clearFilters}>Clear</button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {loading && <div className="loading">Loading complaints...</div>}

        {!loading && complaints.length === 0 && (
          <div className="card empty-state">
            <p>No complaints found.</p>
            {user?.role === 'Customer' && (
              <button className="btn btn-primary" style={{ marginTop: 14 }} onClick={() => navigate('/new-complaint')}>
                Register your first complaint
              </button>
            )}
          </div>
        )}

        {!loading && complaints.length > 0 && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Customer</th>
                  <th>Agent</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {complaints.map(c => (
                  <tr key={c.complaint_id} onClick={() => navigate(`/complaints/${c.complaint_id}`)}>
                    <td><strong>{c.complaint_code}</strong></td>
                    <td>{c.title}</td>
                    <td>{c.category_name}</td>
                    <td><PriorityBadge priority={c.priority} /></td>
                    <td>
                      <StatusBadge status={c.status} />{' '}
                      <SlaBadge breached={c.sla_breached} />
                    </td>
                    <td>{c.customer_name}</td>
                    <td>{c.agent_name || <span style={{ color: '#a0aec0' }}>—</span>}</td>
                    <td>{new Date(c.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}
