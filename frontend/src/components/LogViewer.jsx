const LEVEL_COLORS = { ERROR: 'var(--red)', WARNING: 'var(--amber)', INFO: 'var(--blue)', DEBUG: 'var(--text-muted)' }

export default function LogViewer({ logs, filter }) {
  const visible = filter ? logs.filter(l => l.level === filter) : logs

  if (!visible.length) {
    return (
      <div className="empty-state" style={{ padding: 32 }}>
        <div style={{ fontSize: '0.9rem' }}>No log entries yet. Logs will appear here in real-time.</div>
      </div>
    )
  }

  return (
    <div style={{ fontFamily: 'monospace', fontSize: '0.8125rem' }}>
      {visible.map((entry, i) => (
        <div key={i} style={{
          display: 'flex', gap: 12,
          padding: '6px 12px',
          borderBottom: '1px solid rgba(255,255,255,0.04)',
          color: 'var(--text-primary)',
          background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)',
          transition: 'background 0.15s',
        }}>
          <span style={{ color: 'var(--text-muted)', whiteSpace: 'nowrap', flexShrink: 0 }}>
            {new Date(entry.time * 1000).toLocaleTimeString()}
          </span>
          <span style={{ color: LEVEL_COLORS[entry.level] || 'var(--text-muted)', width: 56, flexShrink: 0, fontWeight: 700 }}>
            {entry.level}
          </span>
          <span style={{ color: 'var(--text-secondary)', flexShrink: 0, maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {entry.logger}
          </span>
          <span style={{ color: 'var(--text-primary)', flex: 1 }}>
            {entry.message}
          </span>
        </div>
      ))}
    </div>
  )
}
