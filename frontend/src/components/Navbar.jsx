import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Radio, ListChecks, History,
  Settings, Terminal, LogOut, TrendingUp
} from 'lucide-react'
import api from '../lib/api'

const NAV_ITEMS = [
  { to: '/',         icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/sources',  icon: Radio,           label: 'Sources'   },
  { to: '/queue',    icon: ListChecks,      label: 'Queue'     },
  { to: '/history',  icon: History,         label: 'History'   },
  { to: '/settings', icon: Settings,        label: 'Settings'  },
  { to: '/logs',     icon: Terminal,        label: 'Live Logs' },
]

export default function Navbar() {
  const navigate = useNavigate()

  const handleLogout = async () => {
    try { await api.post('/auth/logout') } catch (_) {}
    localStorage.removeItem('token')
    navigate('/login')
  }

  return (
    <header style={{
      position: 'fixed', top: 0, left: 0, right: 0, 
      height: 'var(--navbar-h)',
      background: 'var(--bg-glass)',
      backdropFilter: 'blur(16px)',
      WebkitBackdropFilter: 'blur(16px)',
      borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      padding: '0 32px',
      zIndex: 1000,
    }}>
      {/* Left side: Logo */}
      <div style={{ display: 'flex', alignItems: 'center', flex: '1 1 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            width: 38, height: 38, borderRadius: 10,
            background: 'linear-gradient(135deg, var(--accent), var(--accent-dark))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 16px var(--accent-glow)',
          }}>
            <TrendingUp size={20} color="#fff" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--text-primary)', lineHeight: 1.2 }}>NEPSE Bot</div>
            <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', letterSpacing: '0.05em', fontWeight: 600 }}>AUTO POSTER</div>
          </div>
        </div>
      </div>

      {/* Center: Nav Links */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: 8, height: '100%', justifyContent: 'center' }}>
        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '0 16px',
              height: 'calc(var(--navbar-h) - 1px)',
              fontSize: '0.875rem',
              fontWeight: 600,
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderBottom: isActive ? '3px solid var(--accent)' : '3px solid transparent',
              background: isActive ? 'var(--bg-elevated)' : 'transparent',
              transition: 'all var(--transition)',
              textDecoration: 'none',
            })}
          >
            <Icon size={16} style={{ color: 'inherit' }} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Right side: Logout */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', flex: '1 1 0' }}>
        <button
          onClick={handleLogout}
          className="btn btn-ghost btn-sm"
          style={{ display: 'flex', alignItems: 'center', gap: 8 }}
        >
          <LogOut size={16} /> Log out
        </button>
      </div>
    </header>
  )
}
