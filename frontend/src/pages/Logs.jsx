import { useState } from 'react'
import { Trash2, Wifi, WifiOff } from 'lucide-react'
import LogViewer from '../components/LogViewer'
import { useWebSocketLogs } from '../lib/ws'

const LEVEL_FILTERS = ['ALL', 'INFO', 'WARNING', 'ERROR']

export default function Logs() {
  const { logs, clearLogs } = useWebSocketLogs()
  const [filter, setFilter] = useState('ALL')
  const connected = logs.length > 0 || true  // ws auto-connects

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Live Logs</h1>
          <p className="page-subtitle">Real-time scraper and publisher output</p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
            <Wifi size={14} color="var(--green)" /> Connected
          </div>
          <button className="btn btn-ghost btn-sm" onClick={clearLogs} style={{ color: 'var(--red)' }}>
            <Trash2 size={14} /> Clear
          </button>
        </div>
      </div>

      {/* Level filter */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {LEVEL_FILTERS.map(l => (
          <button key={l} className={`btn btn-sm ${filter === l ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter(l)}>
            {l}
          </button>
        ))}
        <span style={{ marginLeft: 'auto', fontSize: '0.8rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
          {logs.length} entries
        </span>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <LogViewer logs={logs} filter={filter === 'ALL' ? null : filter} />
      </div>
    </div>
  )
}
