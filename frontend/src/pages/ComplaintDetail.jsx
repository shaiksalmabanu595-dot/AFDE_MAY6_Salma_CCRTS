import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { StatusBadge, PriorityBadge, SlaBadge } from '../components/Badges'
import { complaintsAPI, usersAPI, feedbackAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'

const STATUSES = ['Open', 'Assigned', 'In Progress', 'Pending Customer Response', 'Escalated', 'Resolved', 'Closed']

export default function ComplaintDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()

  const [complaint, setComplaint] = useState(null)
  const [history, setHistory] = useState([])
  const [agents, setAgents] = useState([])
  const [feedback, setFeedback] = useState(null)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')
  const [loading, setLoading] = useState(true)

  // form state
  const [newStatus, setNewStatus] = useState('')
  const [statusComment, setStatusComment] = useState('')
  const [selectedAgent, setSelectedAgent] = useState('')
  const [rating, setRating] = useState(5)
  const [fbComment, setFbComment] = useState('')

  const reload = async () => {
    try {
      const [cRes, hRes] = await Promise.all([
        complaintsAPI.get(id),
        complaintsAPI.getHistory(id),
      ])
      setComplaint(cRes.data)
      setHistory(hRes.data)
      setNewStatus(cRes.data.status)

      // Try to load feedback (may not exist)
      try {
        const fbRes = await feedbackAPI.get(id)
        setFeedback(fbRes.data)
      } catch { setFeedback(null) }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load complaint')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    reload()
    if (user?.role === 'Admin' || user?.role === 'Supervisor') {
      usersAPI.listAgents().then(({ data }) => setAgents(data)).catch(() => {})
    }
  }, [id])

  const handleAssign = async (e) => {
    e.preventDefault()
    if (!selectedAgent) { setError('Pick an agent'); return }
    try {
      await complaintsAPI.assign(id, Number(selectedAgent))
      setMsg('Complaint assigned successfully'); setError('')
      reload()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to assign')
    }
  }

  const handleStatusUpdate = async (e) => {
    e.preventDefault()
    try {
      await complaintsAPI.updateStatus(id, newStatus, statusComment)
      setMsg(`Status updated to ${newStatus}`); setError(''); setStatusComment('')
      reload()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update status')
    }
  }

  const handleCustomerClose = async () => {
    if (!window.confirm('Close this complaint? This will mark it as fully resolved.')) return
    try {
      await complaintsAPI.updateStatus(id, 'Closed', 'Customer confirmed resolution')
      setMsg('Complaint closed'); setError('')
      reload()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to close')
    }
  }

  const handleFeedback = async (e) => {
    e.preventDefault()
    try {
      await feedbackAPI.submit(id, { rating: Number(rating), comments: fbComment })
      setMsg('Feedback submitted'); setError('')
      reload()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit feedback')
    }
  }

  if (loading) return <><Navbar /><div className="container loading">Loading...</div></>
  if (error && !complaint) return <><Navbar /><div className="container"><div className="alert alert-error">{error}</div></div></>
  if (!complaint) return null

  const isAdmin = user?.role === 'Admin' || user?.role === 'Supervisor'
  const isAgent = user?.role === 'Agent'
  const isOwner = user?.user_id === complaint.customer_id
  const canChangeStatus = isAdmin || (isAgent && complaint.assigned_to === user?.user_id)
  const canGiveFeedback = isOwner && (complaint.status === 'Resolved' || complaint.status === 'Closed') && !feedback
  const canCustomerClose = isOwner && complaint.status === 'Resolved'

  return (
    <>
      <Navbar />
      <div className="container">
        <button className="btn btn-secondary btn-sm" onClick={() => navigate('/complaints')} style={{ marginBottom: 16 }}>
          ← Back to list
        </button>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 18, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 className="page-title" style={{ marginBottom: 6 }}>{complaint.title}</h2>
            <div style={{ color: '#718096', fontSize: '0.9rem' }}>
              <strong>{complaint.complaint_code}</strong> · Filed by {complaint.customer_name}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <PriorityBadge priority={complaint.priority} />
            <StatusBadge status={complaint.status} />
            <SlaBadge breached={complaint.sla_breached} />
          </div>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {msg && <div className="alert alert-success">{msg}</div>}

        <div className="detail-grid">
          <div>
            <div className="card">
              <div className="detail-section">
                <h3>Description</h3>
                <p style={{ whiteSpace: 'pre-wrap', color: '#2d3748', lineHeight: 1.6 }}>
                  {complaint.description}
                </p>
              </div>
            </div>

            <div className="card">
              <div className="detail-section">
                <h3>History</h3>
                {history.length === 0 ? (
                  <p style={{ color: '#a0aec0' }}>No history yet</p>
                ) : (
                  <ul className="timeline">
                    {history.map(h => (
                      <li key={h.history_id}>
                        <div className="time">{new Date(h.updated_at).toLocaleString()}</div>
                        <div className="change">
                          {h.old_status ? `${h.old_status} → ${h.new_status}` : `Created as ${h.new_status}`}
                          {' · by '}{h.updated_by_name}
                        </div>
                        {h.comment && <div className="comment">"{h.comment}"</div>}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {feedback && (
              <div className="card">
                <div className="detail-section">
                  <h3>Customer Feedback</h3>
                  <div style={{ fontSize: '1.5rem', color: '#dd6b20', marginBottom: 8 }}>
                    {'★'.repeat(feedback.rating)}{'☆'.repeat(5 - feedback.rating)} ({feedback.rating}/5)
                  </div>
                  {feedback.comments && <p style={{ color: '#4a5568' }}>"{feedback.comments}"</p>}
                </div>
              </div>
            )}
          </div>

          <div>
            <div className="card">
              <div className="detail-section">
                <h3>Details</h3>
                <div className="detail-row"><span className="label">Category</span><span className="value">{complaint.category_name}</span></div>
                <div className="detail-row"><span className="label">Priority</span><span className="value">{complaint.priority}</span></div>
                <div className="detail-row"><span className="label">Status</span><span className="value">{complaint.status}</span></div>
                <div className="detail-row"><span className="label">SLA</span><span className="value">{complaint.sla_hours} hours</span></div>
                <div className="detail-row"><span className="label">Assigned to</span><span className="value">{complaint.agent_name || 'Unassigned'}</span></div>
                <div className="detail-row"><span className="label">Created</span><span className="value">{new Date(complaint.created_at).toLocaleString()}</span></div>
                {complaint.resolved_at && <div className="detail-row"><span className="label">Resolved</span><span className="value">{new Date(complaint.resolved_at).toLocaleString()}</span></div>}
                {complaint.closed_at && <div className="detail-row"><span className="label">Closed</span><span className="value">{new Date(complaint.closed_at).toLocaleString()}</span></div>}
              </div>
            </div>

            {isAdmin && (
              <div className="card">
                <div className="detail-section">
                  <h3>Assign to Agent</h3>
                  <form onSubmit={handleAssign}>
                    <div className="form-group">
                      <select value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value)} required>
                        <option value="">— Select agent —</option>
                        {agents.map(a => (
                          <option key={a.user_id} value={a.user_id}>{a.name} ({a.email})</option>
                        ))}
                      </select>
                    </div>
                    <button className="btn btn-primary btn-block" type="submit">
                      {complaint.assigned_to ? 'Reassign' : 'Assign'}
                    </button>
                  </form>
                </div>
              </div>
            )}

            {canChangeStatus && (
              <div className="card">
                <div className="detail-section">
                  <h3>Update Status</h3>
                  <form onSubmit={handleStatusUpdate}>
                    <div className="form-group">
                      <select value={newStatus} onChange={(e) => setNewStatus(e.target.value)}>
                        {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </div>
                    <div className="form-group">
                      <textarea
                        placeholder="Comment (optional)"
                        value={statusComment}
                        onChange={(e) => setStatusComment(e.target.value)}
                        rows={3}
                      />
                    </div>
                    <button className="btn btn-success btn-block" type="submit">Update Status</button>
                  </form>
                </div>
              </div>
            )}

            {canCustomerClose && (
              <div className="card">
                <div className="detail-section">
                  <h3>Resolution</h3>
                  <p style={{ fontSize: '0.9rem', color: '#4a5568', marginBottom: 12 }}>
                    Your complaint has been marked as resolved. If you're satisfied, please close it.
                  </p>
                  <button className="btn btn-success btn-block" onClick={handleCustomerClose}>
                    Confirm & Close
                  </button>
                </div>
              </div>
            )}

            {canGiveFeedback && (
              <div className="card">
                <div className="detail-section">
                  <h3>Rate the Resolution</h3>
                  <form onSubmit={handleFeedback}>
                    <div className="form-group">
                      <label>Rating</label>
                      <select value={rating} onChange={(e) => setRating(e.target.value)}>
                        {[5, 4, 3, 2, 1].map(r => (
                          <option key={r} value={r}>{'★'.repeat(r)} ({r}/5)</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group">
                      <textarea
                        placeholder="Comments (optional)"
                        value={fbComment}
                        onChange={(e) => setFbComment(e.target.value)}
                        rows={3}
                      />
                    </div>
                    <button className="btn btn-primary btn-block" type="submit">Submit Feedback</button>
                  </form>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  )
}
