import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  if (!user) return null

  return (
    <nav className="navbar">
      <h1>CCRTS · Complaint Tracker</h1>
      <div className="navbar-links">
        <Link to="/dashboard">Dashboard</Link>
        <Link to="/complaints">Complaints</Link>
        {user.role === 'Customer' && <Link to="/new-complaint">New Complaint</Link>}
        {user.role === 'Admin' && <Link to="/users">Users</Link>}
        <span className="user-info">{user.name} ({user.role})</span>
        <button onClick={handleLogout}>Logout</button>
      </div>
    </nav>
  )
}
