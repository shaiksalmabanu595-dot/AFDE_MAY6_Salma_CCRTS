import { useState, useEffect } from 'react'
import Navbar from '../components/Navbar'
import { usersAPI } from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function Users() {
  const { user } = useAuth()
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('')

  useEffect(() => {
    usersAPI.list()
      .then(({ data }) => setUsers(data))
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load users'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = users.filter(u => {
    if (roleFilter && u.role_name !== roleFilter) return false
    if (search) {
      const s = search.toLowerCase()
      if (!u.name.toLowerCase().includes(s) && !u.email.toLowerCase().includes(s)) return false
    }
    return true
  })

  if (user?.role !== 'Admin' && user?.role !== 'Supervisor') {
    return (
      <>
        <Navbar />
        <div className="container">
          <div className="alert alert-error">Access denied. This page is for Admins and Supervisors only.</div>
        </div>
      </>
    )
  }

  const roles = [...new Set(users.map(u => u.role_name))]

  return (
    <>
      <Navbar />
      <div className="container">
        <h2 className="page-title">User Management</h2>

        <div className="filters">
          <input
            placeholder="Search by name or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
            <option value="">All Roles</option>
            {roles.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {loading && <div className="loading">Loading users...</div>}

        {!loading && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Role</th>
                  <th>Registered</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr><td colSpan={6} style={{ textAlign: 'center', color: '#a0aec0', padding: 30 }}>No users match the filters</td></tr>
                ) : filtered.map(u => (
                  <tr key={u.user_id} style={{ cursor: 'default' }}>
                    <td>{u.user_id}</td>
                    <td><strong>{u.name}</strong></td>
                    <td>{u.email}</td>
                    <td>{u.phone || <span style={{ color: '#a0aec0' }}>—</span>}</td>
                    <td><span className="badge badge-status-Assigned">{u.role_name}</span></td>
                    <td>{new Date(u.created_at).toLocaleDateString()}</td>
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
