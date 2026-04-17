import { useEffect, useState } from 'react'
import { Save, Eye, EyeOff } from 'lucide-react'
import api from '../lib/api'

const SETTING_FIELDS = [
  { key: 'fb_page_access_token', label: 'Facebook Page Access Token', type: 'password', placeholder: 'Long-lived Page Access Token from Meta Dev Portal' },
  { key: 'fb_page_id',           label: 'Facebook Page ID',           type: 'text',     placeholder: 'Numeric page ID' },
  { key: 'caption_template',     label: 'Caption Template',           type: 'textarea', placeholder: '📰 {title}\n\n🔗 {source} | {date}\n\n{hashtags}' },
  { key: 'default_hashtags',     label: 'Default Hashtags',           type: 'text',     placeholder: '#NEPSE #ShareMarket #Nepal' },
  { key: 'scrape_interval_minutes', label: 'Scrape Interval (minutes)', type: 'number', placeholder: '30' },
  { key: 'max_posts_per_day',    label: 'Max Posts Per Day',          type: 'number',   placeholder: '4' },
  { key: 'quiet_hours_start',    label: 'Quiet Hours Start (0–23)',   type: 'number',   placeholder: '22' },
  { key: 'quiet_hours_end',      label: 'Quiet Hours End (0–23)',     type: 'number',   placeholder: '6' },
  { key: 'keyword_filter',       label: 'Keyword Filter (comma-separated)', type: 'textarea', placeholder: 'NEPSE, share market, IPO, सेयर, बजार' },
]

export default function Settings() {
  const [values, setValues] = useState({})
  const [autoApprove, setAutoApprove] = useState(false)
  const [showToken, setShowToken] = useState(false)
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    const r = await api.get('/settings')
    setValues(r.data)
    setAutoApprove(r.data.auto_approve === 'true')
  }

  useEffect(() => { load() }, [])

  const save = async () => {
    setLoading(true)
    try {
      const items = [
        ...Object.entries(values).map(([key, value]) => ({ key, value: String(value) })),
        { key: 'auto_approve', value: String(autoApprove) },
      ]
      await api.put('/settings', items)
      setSaved(true)
      setTimeout(() => setSaved(false), 2500)
    } finally { setLoading(false) }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="page-subtitle">Configure the bot behaviour and Facebook integration</p>
        </div>
        <button className="btn btn-primary" onClick={save} disabled={loading}>
          {loading ? <span className="spinner" /> : <Save size={15} />}
          {saved ? '✓ Saved!' : 'Save Settings'}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Facebook Section */}
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <h2 style={{ fontWeight: 700, marginBottom: 20, color: 'var(--accent)' }}>🔗 Facebook Integration</h2>

          {['fb_page_access_token', 'fb_page_id'].map(key => {
            const f = SETTING_FIELDS.find(f => f.key === key)
            return (
              <div className="form-group" key={key}>
                <label className="form-label">{f.label}</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input
                    className="form-input"
                    type={key === 'fb_page_access_token' && !showToken ? 'password' : 'text'}
                    placeholder={f.placeholder}
                    value={values[key] || ''}
                    onChange={e => setValues(v => ({ ...v, [key]: e.target.value }))}
                  />
                  {key === 'fb_page_access_token' && (
                    <button type="button" className="btn btn-ghost" onClick={() => setShowToken(s => !s)}>
                      {showToken ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Scheduling */}
        <div className="card">
          <h2 style={{ fontWeight: 700, marginBottom: 16, color: 'var(--blue)' }}>⏱ Scheduling</h2>
          
          <div style={{ 
            backgroundColor: 'rgba(56, 189, 248, 0.1)', 
            borderLeft: '4px solid var(--blue)', 
            padding: '12px 16px', 
            marginBottom: 24, 
            borderRadius: '0 8px 8px 0',
            fontSize: '0.875rem', 
            lineHeight: 1.5,
            color: 'var(--text-secondary)' 
          }}>
            <strong>How it works:</strong> The background bot wakes up periodically based on your interval to parse all active sources. Any posts reaching the "Approved" queue will not be published all at once. Instead, the bot will slowly <em>drip-feed</em> them to your Facebook audience one item at a time, strictly respecting your maximum daily limit to prevent spam. The bot will automatically halt all publications during your specified quiet hours.
          </div>

          {['scrape_interval_minutes','max_posts_per_day','quiet_hours_start','quiet_hours_end'].map(key => {
            const f = SETTING_FIELDS.find(f => f.key === key)
            return (
              <div className="form-group" key={key}>
                <label className="form-label">{f.label}</label>
                <input className="form-input" type="number" placeholder={f.placeholder} value={values[key] || ''} onChange={e => setValues(v => ({ ...v, [key]: e.target.value }))} />
              </div>
            )
          })}
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', fontWeight: 600 }}>Auto-Approve Posts</span>
            <label className="toggle">
              <input type="checkbox" checked={autoApprove} onChange={e => setAutoApprove(e.target.checked)} />
              <span className="toggle-slider" />
            </label>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {autoApprove ? 'Posts auto-publish without review' : 'Manual review required'}
            </span>
          </div>
        </div>

        {/* Caption + Keywords */}
        <div className="card">
          <h2 style={{ fontWeight: 700, marginBottom: 20, color: 'var(--green)' }}>✏️ Caption & Keywords</h2>
          {['caption_template', 'default_hashtags', 'keyword_filter'].map(key => {
            const f = SETTING_FIELDS.find(f => f.key === key)
            return (
              <div className="form-group" key={key}>
                <label className="form-label">{f.label}</label>
                {f.type === 'textarea'
                  ? <textarea className="form-textarea" placeholder={f.placeholder} value={values[key] || ''} onChange={e => setValues(v => ({ ...v, [key]: e.target.value }))} />
                  : <input className="form-input" type="text" placeholder={f.placeholder} value={values[key] || ''} onChange={e => setValues(v => ({ ...v, [key]: e.target.value }))} />
                }
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
