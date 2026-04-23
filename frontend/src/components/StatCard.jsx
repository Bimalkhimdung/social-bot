export default function StatCard({ label, value, icon: Icon, color = 'var(--accent)', trend, onClick }) {
  return (
    <div 
      className="card fade-in" 
      style={{ 
        position: 'relative', 
        overflow: 'hidden', 
        cursor: onClick ? 'pointer' : 'default',
        padding: '20px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: 12
      }}
      onClick={onClick}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          {label}
        </div>
        <div style={{ opacity: 0.15, color: '#fff' }}>
          <Icon size={24} strokeWidth={1.5} />
        </div>
      </div>

      <div style={{ 
        fontSize: (value?.toString().length > 6) ? '1.5rem' : '2.5rem', 
        fontWeight: 800, 
        color: 'var(--text-primary)', 
        lineHeight: 1.2, 
        letterSpacing: '-0.02em',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis'
      }}>
        {value ?? '—'}
      </div>

      {trend && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', fontWeight: 600, color: trend.startsWith('+') ? 'var(--green)' : 'var(--text-muted)' }}>
          {trend}
        </div>
      )}
    </div>
  )
}
