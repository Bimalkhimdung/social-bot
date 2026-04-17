import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Send, Edit2, X, Save } from 'lucide-react'
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

  const load = async () => {
    setLoading(true)
    try {
      const q = filter === 'all' ? '' : `&status=${filter}`
      const r = await api.get(`/queue?page=${page}&limit=20${q}`)
      setPosts(r.data)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [filter, page])

  const approve = async (id) => {
    await api.put(`/queue/${id}/approve`)
    load()
  }
  const reject = async (id) => {
    await api.put(`/queue/${id}/reject`)
    load()
  }
  const publishNow = async (id) => {
    await api.post(`/queue/${id}/publish-now`)
    load()
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
        <button className="btn btn-secondary" onClick={load}>Refresh</button>
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
                        <button className="btn btn-success btn-sm" onClick={() => approve(post.id)}>
                          <CheckCircle size={13} /> Approve
                        </button>
                      )}
                      <button className="btn btn-primary btn-sm" onClick={() => publishNow(post.id)}>
                        <Send size={13} /> Publish
                      </button>
                      <button className="btn btn-ghost btn-sm" onClick={() => { setEditingId(post.id); setEditCaption(post.caption || '') }}>
                        <Edit2 size={13} /> Edit
                      </button>
                      <button className="btn btn-ghost btn-sm" style={{ color: 'var(--red)' }} onClick={() => reject(post.id)}>
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
    </div>
  )
}
