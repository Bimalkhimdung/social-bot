export default function HealthCheck({ stats }) {
  const autoCount = stats?.auto_approved_count || 0
  const recentAuto = stats?.recent_auto_posts || []

  // Helper for relative time
  const timeOnly = (date) => {
    if (!date) return '--:--:--'
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  }

  return (
    <div className="card" style={{ height: 420, display: 'flex', flexDirection: 'column' }}>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff', marginBottom: 24 }}>System Health</h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, flex: 1 }}>
        {/* Real Metric: Auto-Approved Count */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Auto-Approved News</span>
            <span style={{ fontWeight: 700, color: 'var(--accent)' }}>{autoCount} items</span>
          </div>
          <div className="progress-track" style={{ height: 4 }}>
            <div 
              className="progress-fill" 
              style={{ width: `${Math.min(100, (autoCount / 500) * 100)}%`, background: 'var(--accent)', height: '100%' }} 
            />
          </div>
        </div>

        {/* Placeholder Metrics (Kept for UI balance as requested by screenshot) */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Proxy Pool</span>
            <span style={{ fontWeight: 700, color: 'var(--blue)' }}>98.2% Active</span>
          </div>
          <div className="progress-track" style={{ height: 4 }}>
            <div className="progress-fill" style={{ width: '98%', background: 'var(--blue)', height: '100%' }} />
          </div>
        </div>
      </div>

      <div style={{ marginTop: 'auto' }}>
        <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12 }}>
          Recent Auto-Posts
        </div>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {recentAuto.length === 0 ? (
            <div className="log-snippet" style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>No automated posts yet.</div>
          ) : (
            recentAuto.map((post, i) => (
              <div className="log-snippet" key={i} style={{ borderRadius: 6, padding: '8px 12px' }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span style={{ color: 'var(--blue)', fontWeight: 600, fontSize: '0.75rem', minWidth: 65 }}>{timeOnly(post.posted_at)} {'->'}</span>
                  <span style={{ fontSize: '0.75rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {post.title}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

