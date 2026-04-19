import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, ResponsiveContainer, Legend 
} from 'recharts'

const MOCK_DATA = [
  { day: 'MON', articles: 45, success: 38 },
  { day: 'TUE', articles: 62, success: 58 },
  { day: 'WED', articles: 55, success: 52 },
  { day: 'THU', articles: 72, success: 68 },
  { day: 'FRI', articles: 68, success: 65 },
  { day: 'SAT', articles: 48, success: 42 },
  { day: 'SUN', articles: 52, success: 48 },
]

export default function PerformanceChart() {
  return (
    <div className="card" style={{ height: 400, display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#fff' }}>Automation Performance</h2>
        <div style={{ display: 'flex', gap: 16, fontSize: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#3b82f6' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Articles</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981' }} />
            <span style={{ color: 'var(--text-secondary)' }}>Success Rate</span>
          </div>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: 0 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={MOCK_DATA} margin={{ top: 0, right: 0, left: -24, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
            <XAxis 
              dataKey="day" 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: 'var(--text-muted)', fontSize: 10, fontWeight: 600 }}
              dy={10}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{ fill: 'var(--text-muted)', fontSize: 10 }} 
            />
            <Tooltip 
              cursor={{ fill: 'rgba(255,255,255,0.03)' }}
              contentStyle={{ 
                background: 'var(--bg-elevated)', 
                border: '1px solid var(--border)', 
                borderRadius: '8px',
                fontSize: '0.8rem'
              }}
            />
            <Bar 
              dataKey="articles" 
              fill="#3b82f6" 
              radius={[4, 4, 0, 0]} 
              barSize={32}
            />
            <Bar 
              dataKey="success" 
              fill="#10b981" 
              radius={[4, 4, 0, 0]} 
              barSize={32}
              opacity={0.6}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
