import { useEffect, useState } from 'react'
import { BarChart2, Clock, Inbox, Activity, Play, RefreshCw } from 'lucide-react'
import StatCard from '../components/StatCard'
import api from '../lib/api'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [scraping, setScraping] = useState(false)
  const [recentPosts, setRecentPosts] = useState([])

  const loadStats = async () => {
    const [s, p] = await Promise.all([api.get('/stats'), api.get('/posts?limit=5')])
    setStats(s.data)
    setRecentPosts(p.data)
  }

  useEffect(() => {
    loadStats()
    const interval = setInterval(loadStats, 30000)
    return () => clearInterval(interval)
  }, [])

  const triggerScrape = async () => {
    setScraping(true)
    try { await api.post('/scraper/run') } finally { setScraping(false); loadStats() }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">NEPSE Auto-Poster overview</p>
        </div>
        <button className="btn btn-primary" onClick={triggerScrape} disabled={scraping}>
          {scraping ? <span className="spinner" /> : <Play size={15} />}
          {scraping ? 'Scraping…' : 'Scrape Now'}
        </button>
      </div>

      {/* Stat cards */}
      <div className="stat-grid">
        <StatCard label="Posts Today" value={stats?.posts_today} icon={BarChart2} color="var(--accent)" />
        <StatCard label="Pending Queue" value={stats?.pending_count} icon={Inbox} color="var(--amber)" />
        <StatCard label="Total Articles" value={stats?.total_articles} icon={Activity} color="var(--blue)" />
        <StatCard
          label="Last Post"
          value={stats?.last_post_at ? new Date(stats.last_post_at).toLocaleTimeString() : 'None'}
          icon={Clock}
          color="var(--green)"
        />
      </div>

      {/* Scheduler status */}
      <div className="card" style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: stats?.scheduler_running ? 'var(--green)' : 'var(--red)',
            boxShadow: stats?.scheduler_running ? '0 0 8px var(--green)' : 'none',
          }} className={stats?.scheduler_running ? 'pulse' : ''} />
          <span style={{ fontWeight: 700 }}>Scheduler</span>
          <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            {stats?.scheduler_running ? 'Running' : 'Stopped'}
          </span>
          {stats?.scraper_running && (
            <span style={{ marginLeft: 8, fontSize: '0.8rem', color: 'var(--blue)' }}>⟳ Scraping in progress…</span>
          )}
        </div>
      </div>

      {/* Recent posts */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <h2 style={{ fontWeight: 700, fontSize: '1rem' }}>Recent Posts</h2>
          <button className="btn btn-ghost btn-sm" onClick={loadStats}><RefreshCw size={14} /></button>
        </div>

        {recentPosts.length === 0 ? (
          <div className="empty-state" style={{ padding: '24px 0' }}>No posts yet</div>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Title</th><th>Source</th><th>Status</th><th>Posted</th>
                </tr>
              </thead>
              <tbody>
                {recentPosts.map(p => (
                  <tr key={p.id}>
                    <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {p.article?.title}
                    </td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{p.article?.source_name}</td>
                    <td><span className={`badge badge-${p.status}`}>{p.status}</span></td>
                    <td style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                      {p.posted_at ? new Date(p.posted_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
