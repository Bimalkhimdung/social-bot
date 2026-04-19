export default function HealthCheck() {
  const metrics = [
    { label: 'Proxy Pool', value: '98.2% Active', percent: 98, color: 'var(--blue)' },
    { label: 'Engine Load', value: '12%', percent: 12, color: 'var(--accent)' },
    { label: 'API Latency', value: '144ms', percent: 45, color: 'var(--text-muted)' },
  ]

  return (
    <div className="card" style={{ height: 400, display: 'flex', flexDirection: 'column' }}>
      <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff', marginBottom: 24 }}>Health Check</h2>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 24, flex: 1 }}>
        {metrics.map((m, i) => (
          <div key={i}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8, fontSize: '0.85rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>{m.label}</span>
              <span style={{ fontWeight: 700, color: m.color }}>{m.value}</span>
            </div>
            <div className="progress-track" style={{ height: 4 }}>
              <div 
                className="progress-fill" 
                style={{ width: `${m.percent}%`, background: m.color, height: '100%' }} 
              />
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 'auto' }}>
        <div style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8 }}>
          Latest Log
        </div>
        <div className="log-snippet" style={{ borderRadius: 4 }}>
          <div style={{ display: 'flex', gap: 8 }}>
            <span style={{ color: 'var(--blue)', fontWeight: 600 }}>20:01:04 {'->'}</span>
            <span>Successfully synced 1 item from Sharesansar.</span>
          </div>
        </div>
      </div>
    </div>
  )
}
