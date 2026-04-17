import { useEffect, useState } from 'react'
import { Plus, Trash2, Edit2, Play, X, Check } from 'lucide-react'
import SourceForm from '../components/SourceForm'
import api from '../lib/api'

export default function Sources() {
  const [sources, setSources] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState(null)
  const [loading, setLoading] = useState(false)
  const [testResult, setTestResult] = useState({})

  const load = async () => {
    const r = await api.get('/sources')
    setSources(r.data)
  }

  useEffect(() => { load() }, [])

  const handleAdd = async (data) => {
    setLoading(true)
    try {
      await api.post('/sources', data)
      setShowForm(false)
      load()
    } finally { setLoading(false) }
  }

  const handleEdit = async (data) => {
    setLoading(true)
    try {
      await api.put(`/sources/${editing.id}`, data)
      setEditing(null)
      load()
    } finally { setLoading(false) }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this source?')) return
    await api.delete(`/sources/${id}`)
    load()
  }

  const handleTest = async (id) => {
    setTestResult(t => ({ ...t, [id]: { loading: true } }))
    try {
      const r = await api.post(`/sources/${id}/test`)
      setTestResult(t => ({ ...t, [id]: r.data }))
    } catch (e) {
      setTestResult(t => ({ ...t, [id]: { error: 'Test failed' } }))
    }
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Sources</h1>
          <p className="page-subtitle">Manage your news scraping sources</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowForm(true)}>
          <Plus size={16} /> Add Source
        </button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
            <h2 style={{ fontWeight: 700 }}>New Source</h2>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowForm(false)}><X size={16} /></button>
          </div>
          <SourceForm onSubmit={handleAdd} onCancel={() => setShowForm(false)} loading={loading} />
        </div>
      )}

      {/* Sources list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {sources.map(src => (
          <div key={src.id}>
            {editing?.id === src.id ? (
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
                  <h2 style={{ fontWeight: 700 }}>Edit: {src.name}</h2>
                  <button className="btn btn-ghost btn-sm" onClick={() => setEditing(null)}><X size={16} /></button>
                </div>
                <SourceForm
                  initial={{ ...src, selector_config: JSON.stringify(src.selector_config, null, 2) }}
                  onSubmit={handleEdit}
                  onCancel={() => setEditing(null)}
                  loading={loading}
                />
              </div>
            ) : (
              <div className="card">
                <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                      <span style={{ fontWeight: 700, fontSize: '1rem' }}>{src.name}</span>
                      <span className={`badge badge-${src.is_active ? 'approved' : 'rejected'}`}>
                        {src.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <span className="badge badge-pending" style={{ fontSize: '0.65rem' }}>{src.source_type.toUpperCase()}</span>
                    </div>
                    <a href={src.url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)', fontSize: '0.85rem', overflow: 'hidden', textOverflow: 'ellipsis', display:'block', whiteSpace:'nowrap' }}>
                      {src.url}
                    </a>
                    {src.last_scraped_at && (
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
                        Last scraped: {new Date(src.last_scraped_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => handleTest(src.id)}>
                      <Play size={13} /> Test
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => setEditing(src)}><Edit2 size={14} /></button>
                    <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red)' }} onClick={() => handleDelete(src.id)}><Trash2 size={14} /></button>
                  </div>
                </div>

                {/* Test result */}
                {testResult[src.id] && (
                  <div style={{ marginTop: 16, padding: 12, background: 'var(--bg-surface)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)' }}>
                    {testResult[src.id].loading && <div className="spinner" />}
                    {testResult[src.id].error && <span style={{ color: 'var(--red)' }}>{testResult[src.id].error}</span>}
                    {testResult[src.id].preview && (
                      <div>
                        <div style={{ fontWeight: 600, marginBottom: 8, color: 'var(--green)' }}>
                          ✓ Found {testResult[src.id].found} articles — preview:
                        </div>
                        {testResult[src.id].preview.map((item, i) => (
                          <div key={i} style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', borderBottom: '1px solid var(--border)', paddingBottom: 6, marginBottom: 6 }}>
                            <a href={item.article_url} target="_blank" rel="noreferrer" style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{item.title}</a>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {sources.length === 0 && (
          <div className="card">
            <div className="empty-state">
              <Plus size={40} />
              <div>No sources yet. Add a source to get started.</div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
