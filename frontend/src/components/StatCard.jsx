export default function StatCard({ label, value, icon: Icon, color = 'var(--accent)', trend, onClick }) {
  return (
    <div 
      className="card fade-in" 
      style={{ position: 'relative', overflow: 'hidden', cursor: onClick ? 'pointer' : 'default' }}
      onClick={onClick}
    >
      {/* Glow blob */}
      <div style={{
        position: 'absolute', top: -20, right: -20,
        width: 80, height: 80, borderRadius: '50%',
        background: color, opacity: 0.08, filter: 'blur(20px)',
      }} />

      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 8 }}>
            {label}
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', lineHeight: 1 }}>
            {value ?? '—'}
          </div>
          {trend && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 6 }}>{trend}</div>
          )}
        </div>
        <div style={{
          width: 44, height: 44, borderRadius: 12,
          background: `${color}20`,
          border: `1px solid ${color}40`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Icon size={20} color={color} />
        </div>
      </div>
    </div>
  )
}
