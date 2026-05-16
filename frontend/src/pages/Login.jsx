import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authAPI } from '../services/api'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await authAPI.login({ email, password })
      login(data.access_token, data.user)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  const quickFill = (e, em, pw) => {
    e.preventDefault()
    setEmail(em); setPassword(pw)
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h2>Welcome back</h2>
        <p className="subtitle">Sign in to your CCRTS account</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        <p className="auth-footer">
          New customer? <Link to="/register">Register here</Link>
        </p>
        <div className="demo-creds">
          <strong>Demo accounts (click to fill):</strong>
          <div><a href="#" onClick={(e) => quickFill(e, 'admin@ccrts.com', 'admin123')}>Admin</a> · admin@ccrts.com / admin123</div>
          <div><a href="#" onClick={(e) => quickFill(e, 'agent@ccrts.com', 'agent123')}>Agent</a> · agent@ccrts.com / agent123</div>
          <div><a href="#" onClick={(e) => quickFill(e, 'customer@ccrts.com', 'customer123')}>Customer</a> · customer@ccrts.com / customer123</div>
        </div>
      </div>
    </div>
  )
}
