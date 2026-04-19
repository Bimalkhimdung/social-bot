import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Radio, ListChecks, History,
  Settings, TrendingUp, Zap, Bell, User, LogOut, BarChart2
} from 'lucide-react'
import { useState } from 'react'
import { useUI } from '../context/UIContext'
import api from '../lib/api'

const NAV_ITEMS = [
  { to: '/',           icon: LayoutDashboard, label: 'Dashboard'  },
  { to: '/sources',    icon: Radio,           label: 'Sources'    },
  { to: '/queue',      icon: ListChecks,      label: 'Queue'      },
  { to: '/history',    icon: History,         label: 'History'    },
  { to: '/settings',   icon: Settings,        label: 'Settings'   },
  { to: '/daily-post', icon: BarChart2,       label: 'Daily Post' },
]

export default function Navbar() {
  const navigate = useNavigate()
  const { confirm, showToast } = useUI()
  const [scraping, setScraping] = useState(false)

  const handleLogout = async () => {
    try { await api.post('/auth/logout') } catch (_) {}
    localStorage.removeItem('token')
    navigate('/login')
  }

  const triggerGlobalScrape = () => {
    confirm({
      title: 'Trigger Scraper?',
      message: 'This will start a manual scraping cycle across all active sources. New articles will appear in the queue.',
      type: 'primary',
      onConfirm: async () => {
        setScraping(true)
        showToast('Scraper started', 'primary')
        
        try {
          await api.post('/scraper/run')
          
          // Start polling for completion
          const pollInterval = setInterval(async () => {
            try {
              const { data } = await api.get('/scraper/status')
              if (!data.running) {
                clearInterval(pollInterval)
                setScraping(false)
                
                const stats = data.last_run_stats || {}
                const resultMsg = `Scrape Finish: ${stats.new || 0} New, ${stats.skipped_dedup || 0} Skipped, ${stats.skipped_kw || 0} Filtered`
                showToast(resultMsg, 'success')
              }
            } catch (pollErr) {
              clearInterval(pollInterval)
              setScraping(false)
            }
          }, 2000)

        } catch (e) {
          showToast('Failed to start scraper. Please check system logs.', 'error')
          setScraping(false)
        }
      }
    })
  }

  return (
    <header style={{
      position: 'fixed', top: 0, left: 0, right: 0, 
      height: 'var(--navbar-h)',
      background: 'rgba(5, 7, 10, 0.8)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
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
            <div style={{ fontWeight: 800, fontSize: '0.95rem', color: 'var(--text-primary)', lineHeight: 1.2, letterSpacing: '-0.02em' }}>NEPSE Bot</div>
            <div style={{ fontSize: '0.6rem', color: 'var(--text-muted)', letterSpacing: '0.05em', fontWeight: 700 }}>AUTO POSTER</div>
          </div>
        </div>
      </div>

      {/* Center: Nav Links */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: 4, height: '100%', justifyContent: 'center' }}>
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
              fontSize: '0.85rem',
              fontWeight: 600,
              color: isActive ? '#fff' : 'var(--text-secondary)',
              borderBottom: isActive ? '2px solid #fff' : '2px solid transparent',
              transition: 'all var(--transition)',
              textDecoration: 'none',
              opacity: isActive ? 1 : 0.7
            })}
          >
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Right side: Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', flex: '1 1 0', gap: 20 }}>
        <button
          onClick={triggerGlobalScrape}
          className="btn btn-blue"
          disabled={scraping}
          style={{ padding: '8px 16px', fontSize: '0.8rem', borderRadius: 8 }}
        >
          <Zap size={14} fill="currentColor" /> {scraping ? 'Scraping...' : 'Scrape Now'}
        </button>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: 'var(--text-secondary)' }}>
          <button className="btn btn-ghost btn-sm" style={{ padding: 4 }}><Bell size={18} /></button>
          <button className="btn btn-ghost btn-sm" style={{ padding: 4 }}><User size={20} /></button>
          <button
            onClick={handleLogout}
            title="Logo out"
            className="btn btn-ghost btn-sm"
            style={{ padding: 4 }}
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </header>
  )
}

