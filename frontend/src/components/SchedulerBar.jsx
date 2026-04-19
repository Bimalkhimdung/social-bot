import { Activity, Clock } from 'lucide-react'

export default function SchedulerBar({ running, monitoring = [], nextSync, version = 'v2.4.0-stable' }) {
  return (
    <div className="status-bar fade-in">
      {/* Pulse Badge */}
      <div style={{
        padding: '4px 12px',
        borderRadius: 6,
        background: running ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
        border: running ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
        color: running ? 'var(--green)' : 'var(--red)',
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        fontWeight: 800,
        fontSize: '0.65rem',
        letterSpacing: '0.05em',
        textTransform: 'uppercase'
      }}>
        <div style={{
          width: 6, height: 6, borderRadius: '50%',
          background: running ? 'var(--green)' : 'var(--red)',
          boxShadow: running ? '0 0 8px var(--green)' : 'none'
        }} className={running ? 'pulse' : ''} />
        Scheduler {running ? 'Running' : 'Stopped'}
      </div>

      {/* Monitoring List */}
      <div style={{ display: 'flex', gap: 16, overflow: 'hidden', whiteSpace: 'nowrap', flex: 1 }}>
        {monitoring.map((m, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text-muted)', fontSize: '0.75rem' }}>
            <Activity size={12} />
            Monitoring: <span style={{ color: 'var(--text-secondary)' }}>{m}</span>
          </div>
        ))}
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem' }}>
          <Clock size={12} />
          <span>Next sync in <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{nextSync || '--:--'}</span></span>
        </div>
        <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontStyle: 'italic' }}>
          {version}
        </div>
      </div>
    </div>
  )
}
