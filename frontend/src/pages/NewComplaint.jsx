import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import Navbar from '../components/Navbar'
import { complaintsAPI, categoriesAPI } from '../services/api'

export default function NewComplaint() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState([])
  const [form, setForm] = useState({
    category_id: '', title: '', description: '', priority: 'Medium',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    categoriesAPI.list()
      .then(({ data }) => {
        setCategories(data)
        if (data.length > 0) setForm(f => ({ ...f, category_id: data[0].category_id }))
      })
      .catch((err) => setError(err.response?.data?.detail || 'Could not load categories'))
  }, [])

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const payload = { ...form, category_id: Number(form.category_id) }
      const { data } = await complaintsAPI.create(payload)
      navigate(`/complaints/${data.complaint_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create complaint')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <Navbar />
      <div className="container">
        <h2 className="page-title">Register a New Complaint</h2>
        <div className="card" style={{ maxWidth: 700 }}>
          {error && <div className="alert alert-error">{error}</div>}
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title *</label>
              <input
                name="title" value={form.title} onChange={handleChange}
                placeholder="Brief summary of the issue" required maxLength={200}
              />
            </div>

            <div className="form-group">
              <label>Category *</label>
              <select name="category_id" value={form.category_id} onChange={handleChange} required>
                {categories.map(c => (
                  <option key={c.category_id} value={c.category_id}>{c.category_name}</option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label>Priority *</label>
              <select name="priority" value={form.priority} onChange={handleChange}>
                <option value="Low">Low (SLA: 72 hours)</option>
                <option value="Medium">Medium (SLA: 48 hours)</option>
                <option value="High">High (SLA: 24 hours)</option>
                <option value="Critical">Critical (SLA: 4 hours)</option>
              </select>
            </div>

            <div className="form-group">
              <label>Description *</label>
              <textarea
                name="description" value={form.description} onChange={handleChange}
                placeholder="Describe your issue in detail..." rows={6} required
              />
            </div>

            <div style={{ display: 'flex', gap: 10 }}>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Submitting...' : 'Submit Complaint'}
              </button>
              <button type="button" className="btn btn-secondary" onClick={() => navigate('/complaints')}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
