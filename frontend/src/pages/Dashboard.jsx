import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { 
  BarChart2, Clock, Inbox, Activity, 
  ExternalLink, Sliders
} from 'lucide-react'
import StatCard from '../components/StatCard'
import SchedulerBar from '../components/SchedulerBar'
import PerformanceChart from '../components/PerformanceChart'
import HealthCheck from '../components/HealthCheck'
import api from '../lib/api'

// Helper for relative time
const timeAgo = (date) => {
  if (!date) return '—'
  const seconds = Math.floor((new Date() - new Date(date)) / 1000)
  let interval = seconds / 31536000
  if (interval > 1) return Math.floor(interval) + ' years ago'
  interval = seconds / 2592000
  if (interval > 1) return Math.floor(interval) + ' months ago'
  interval = seconds / 86400
  if (interval > 1) return Math.floor(interval) + ' days ago'
  interval = seconds / 3600
  if (interval > 1) return Math.floor(interval) + ' hours ago'
  interval = seconds / 60
  if (interval > 1) return Math.floor(interval) + ' mins ago'
  return Math.floor(seconds) + ' secs ago'
}

// Helper for source initials
const getInitials = (name) => {
  if (!name) return '??'
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

// Helper for countdown
const timeUntil = (date) => {
  if (!date) return '—'
  const diff = new Date(date) - new Date()
  if (diff <= 0) return 'Any moment'
  const mins = Math.floor(diff / 60000)
  const secs = Math.floor((diff % 60000) / 1000)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recentPosts, setRecentPosts] = useState([])
  const [countdown, setCountdown] = useState('--:--')
  const navigate = useNavigate()

  const loadData = async () => {
    try {
      const [s, p] = await Promise.all([api.get('/stats'), api.get('/posts?limit=8')])
      setStats(s.data)
      setRecentPosts(p.data)
    } catch (e) {}
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  // Timer for countdown
  useEffect(() => {
    if (!stats?.next_scrape_at) return
    const id = setInterval(() => {
      setCountdown(timeUntil(stats.next_scrape_at))
    }, 1000)
    return () => clearInterval(id)
  }, [stats?.next_scrape_at])

  return (
    <div className="fade-in">
      {/* Real-time Status Bar */}
      <SchedulerBar 
        running={stats?.scheduler_running} 
        monitoring={stats?.active_sources || []} 
        nextSync={countdown}
      />

      {/* Main Stats Grid */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(4, 1fr)', gap: 24, marginBottom: 40 }}>
        <StatCard 
          label="Posts Today" 
          value={stats?.posts_today?.toString().padStart(2, '0')} 
          icon={BarChart2} 
          trend="+20% from yesterday" 
        />
        <StatCard 
          label="Pending Queue" 
          value={stats?.pending_count?.toString().padStart(2, '0')} 
          icon={Inbox} 
          trend="Processing active" 
          onClick={() => navigate('/queue')}
        />
        <StatCard 
          label="Total Articles" 
          value={stats?.total_articles} 
          icon={Activity} 
          trend="Database healthy" 
        />
        <StatCard
          label="Last Post"
          value={stats?.last_post_at ? 
            new Date(stats.last_post_at).toLocaleString('en-US', { 
              timeZone: 'Asia/Kathmandu', 
              month: 'short', day: 'numeric', 
              hour: '2-digit', minute: '2-digit',
              hour12: false 
            }) : 'None'}
          icon={Clock}
          trend="Nepal Standard Time"
        />
      </div>

      {/* Recent Scrapes Section */}
      <div className="card" style={{ padding: '0 0 12px 0', border: 'none', background: 'transparent', boxShadow: 'none', marginBottom: 40 }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 24, padding: '0 8px' }}>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#fff', marginBottom: 6 }}>Recent Scrapes</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Real-time feed of automated content extraction.</p>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <button className="btn btn-secondary btn-sm" style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 6 }} onClick={() => navigate('/history')}>
              View All
            </button>
            <button className="btn btn-secondary btn-sm" style={{ padding: '6px 8px', background: 'rgba(255,255,255,0.05)', borderRadius: 6 }}>
              <Sliders size={14} />
            </button>
          </div>
        </div>

        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div className="table-wrap">
            <table className="table-modern">
              <thead style={{ background: 'rgba(255,255,255,0.02)' }}>
                <tr>
                  <th style={{ padding: '16px 24px' }}>Article Title</th>
                  <th>Source</th>
                  <th>Status</th>
                  <th>Timestamp</th>
                  <th style={{ textAlign: 'right', paddingRight: 24 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {recentPosts.length === 0 ? (
                  <tr><td colSpan="5" style={{ textAlign: 'center', padding: 48, color: 'var(--text-muted)' }}>No recent activity detected.</td></tr>
                ) : (
                  recentPosts.map(p => (
                    <tr key={p.id}>
                      <td style={{ padding: '16px 24px', fontWeight: 500, color: '#fff', maxWidth: 400 }}>
                        <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {p.article?.title}
                        </div>
                      </td>
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          <div className="source-badge">
                            {getInitials(p.article?.source_name)}
                          </div>
                          <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{p.article?.source_name}</span>
                        </div>
                      </td>
                      <td>
                        <span className={`pill pill-${p.status === 'POSTED' ? 'posted' : 'pending'}`}>
                          {p.status}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                        {timeAgo(p.posted_at || p.created_at)}
                      </td>
                      <td style={{ textAlign: 'right', paddingRight: 24 }}>
                        <button className="btn btn-ghost btn-sm" style={{ color: 'var(--text-muted)' }}>
                          <ExternalLink size={14} />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Expanded Analytics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 24, marginBottom: 40 }}>
        <PerformanceChart />
        <HealthCheck stats={stats} />
      </div>
    </div>
  )
}
