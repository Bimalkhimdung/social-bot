import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Send, Edit2, X, Save, DownloadCloud } from 'lucide-react'
import PostCard from '../components/PostCard'
import api from '../lib/api'

const STATUS_FILTERS = ['all', 'pending', 'approved', 'posted', 'rejected']

export default function Queue() {
  const [posts, setPosts] = useState([])
  const [filter, setFilter] = useState('pending')
  const [editingId, setEditingId] = useState(null)
  const [editCaption, setEditCaption] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const [scraping, setScraping] = useState(false)
  const [confirmDialog, setConfirmDialog] = useState(null)

  const load = async () => {
    setLoading(true)
    try {
      const q = filter === 'all' ? '' : `&status=${filter}`
      const r = await api.get(`/queue?page=${page}&limit=20${q}`)
      setPosts(r.data)
    } finally { setLoading(false) }
  }

  const triggerScrape = async () => {
    setScraping(true)
    try {
      await api.post('/scraper/run')
      // Poll for new items after giving the scraper a head start
      setTimeout(load, 3000)
    } catch (e) {
      console.error('Scrape trigger failed', e)
    } finally {
      // Re-enable the button after a cooldown
      setTimeout(() => setScraping(false), 8000)
    }
  }

  useEffect(() => { load() }, [filter, page])

  const requestApprove = (id) => {
    setConfirmDialog({
      message: 'Are you sure you want to approve this post for scheduled publishing?',
      type: 'success',
      onConfirm: async () => {
        await api.put(`/queue/${id}/approve`)
        load()
      }
    })
  }

  const requestReject = (id) => {
    setConfirmDialog({
      message: 'Are you sure you want to permanently reject and delete this post?',
      type: 'danger',
      onConfirm: async () => {
        await api.put(`/queue/${id}/reject`)
        load()
      }
    })
  }

  const requestPublishNow = (id) => {
    setConfirmDialog({
      message: 'Are you sure you want to instantly publish this post to Facebook right now?',
      type: 'primary',
      onConfirm: async () => {
        await api.post(`/queue/${id}/publish-now`)
        load()
      }
    })
  }
  const saveCaption = async (id) => {
    await api.put(`/queue/${id}`, { caption: editCaption })
    setEditingId(null)
    load()
  }

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">Post Queue</h1>
          <p className="page-subtitle">Review, approve, and schedule posts</p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button 
            className="btn btn-primary" 
            onClick={triggerScrape}
            disabled={scraping}
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <DownloadCloud size={16} />
            {scraping ? 'Scraping...' : 'Scrape Now'}
          </button>
          <button className="btn btn-secondary" onClick={load}>Refresh</button>
        </div>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {STATUS_FILTERS.map(s => (
          <button key={s} className={`btn btn-sm ${filter === s ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setFilter(s); setPage(1) }}>
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      {loading && <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}><div className="spinner" /></div>}

      {!loading && posts.length === 0 && (
        <div className="card"><div className="empty-state">No posts in this filter.</div></div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {posts.map(post => (
          <div key={post.id}>
            {/* Caption editor */}
            {editingId === post.id && (
              <div className="card" style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                  <textarea
                    className="form-textarea"
                    value={editCaption}
                    onChange={e => setEditCaption(e.target.value)}
                    rows={4}
                    style={{ flex: 1 }}
                  />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <button className="btn btn-success btn-sm" onClick={() => saveCaption(post.id)}><Save size={14} /> Save</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => setEditingId(null)}><X size={14} /></button>
                  </div>
                </div>
              </div>
            )}

            <PostCard
              post={post}
              actions={
                <>
                  {post.status !== 'posted' && post.status !== 'rejected' && (
                    <>
                      {post.status === 'pending' && (
                        <button className="btn btn-success btn-sm" onClick={() => requestApprove(post.id)}>
                          <CheckCircle size={13} /> Approve
                        </button>
                      )}
                      <button className="btn btn-primary btn-sm" onClick={() => requestPublishNow(post.id)}>
                        <Send size={13} /> Publish
                      </button>
                      <button className="btn btn-ghost btn-sm" onClick={() => { setEditingId(post.id); setEditCaption(post.caption || '') }}>
                        <Edit2 size={13} /> Edit
                      </button>
                      <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red)' }} onClick={() => requestReject(post.id)}>
                        <XCircle size={13} /> Reject
                      </button>
                    </>
                  )}
                </>
              }
            />
          </div>
        ))}
      </div>

      {/* Pagination */}
      {posts.length === 20 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 32 }}>
          {page > 1 && <button className="btn btn-secondary" onClick={() => setPage(p => p - 1)}>← Prev</button>}
          <button className="btn btn-secondary" onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      )}
      {/* Custom Confirmation Modal */}
      {confirmDialog && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(3px)',
          zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div className="card fade-in" style={{ width: 400, maxWidth: '90%', padding: '32px 24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <div style={{ 
              width: 48, height: 48, borderRadius: '50%', marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'center',
              backgroundColor: confirmDialog.type === 'danger' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(56, 189, 248, 0.1)',
              color: confirmDialog.type === 'danger' ? 'var(--red)' : 'var(--blue)'
            }}>
              {confirmDialog.type === 'danger' ? <XCircle size={24} /> : <CheckCircle size={24} />}
            </div>
            <h2 style={{ marginBottom: 12, fontSize: '1.25rem' }}>Are you sure?</h2>
            <p style={{ marginBottom: 28, color: 'var(--text-secondary)', lineHeight: 1.5 }}>{confirmDialog.message}</p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: 12, width: '100%' }}>
              <button 
                className="btn btn-secondary" 
                style={{ flex: 1 }}
                onClick={() => setConfirmDialog(null)}
              >
                Cancel
              </button>
              <button 
                className="btn" 
                style={{ 
                  flex: 1, 
                  backgroundColor: confirmDialog.type === 'danger' ? 'var(--red)' : 'var(--blue)', 
                  color: 'white',
                  border: 'none'
                }}
                onClick={() => {
                  confirmDialog.onConfirm()
                  setConfirmDialog(null)
                }}
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
