import { useState } from 'react'

const DEFAULT_FORM = {
  name: '', url: '', source_type: 'html', is_active: true,
  selector_config: JSON.stringify({
    title_selector: 'h3 a, h5 a',
    link_attr: 'href',
    summary_selector: 'p',
    image_selector: 'img',
    image_attr: 'src',
    base_url: '',
  }, null, 2),
}

export default function SourceForm({ initial, onSubmit, onCancel, loading }) {
  const [form, setForm] = useState(initial || DEFAULT_FORM)
  const [jsonError, setJsonError] = useState('')

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = (e) => {
    e.preventDefault()
    try {
      const selector_config = JSON.parse(form.selector_config)
      onSubmit({ ...form, selector_config })
    } catch (_) {
      setJsonError('Invalid JSON in selector config')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className="form-group">
        <label className="form-label">Source Name</label>
        <input className="form-input" value={form.name} onChange={e => set('name', e.target.value)} required placeholder="e.g. Arthasarokar" />
      </div>

      <div className="form-group">
        <label className="form-label">URL</label>
        <input className="form-input" type="url" value={form.url} onChange={e => set('url', e.target.value)} required placeholder="https://..." />
      </div>

      <div className="form-group">
        <label className="form-label">Source Type</label>
        <select className="form-select" value={form.source_type} onChange={e => set('source_type', e.target.value)}>
          <option value="html">HTML (BeautifulSoup)</option>
          <option value="api">REST API (JSON)</option>
        </select>
      </div>

      <div className="form-group">
        <label className="form-label">Selector Config (JSON)</label>
        <textarea
          className="form-textarea"
          style={{ fontFamily: 'monospace', fontSize: '0.8125rem', minHeight: 160 }}
          value={form.selector_config}
          onChange={e => { set('selector_config', e.target.value); setJsonError('') }}
        />
        {jsonError && <div style={{ color: 'var(--red)', fontSize: '0.8rem' }}>{jsonError}</div>}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
        <label style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Active</label>
        <label className="toggle">
          <input type="checkbox" checked={form.is_active} onChange={e => set('is_active', e.target.checked)} />
          <span className="toggle-slider" />
        </label>
      </div>

      <div style={{ display: 'flex', gap: 12 }}>
        <button type="submit" className="btn btn-primary" disabled={loading}>
          {loading ? <span className="spinner" /> : null}
          {initial ? 'Update Source' : 'Add Source'}
        </button>
        {onCancel && <button type="button" className="btn btn-secondary" onClick={onCancel}>Cancel</button>}
      </div>
    </form>
  )
}
