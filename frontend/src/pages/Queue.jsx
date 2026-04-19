import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, Send, Edit2, X, Save } from 'lucide-react'
import PostCard from '../components/PostCard'
import { useUI } from '../context/UIContext'
import api from '../lib/api'

const STATUS_FILTERS = ['all', 'pending', 'approved', 'posted', 'rejected']

export default function Queue() {
  const [posts, setPosts] = useState([])
  const [filter, setFilter] = useState('pending')
  const [editingId, setEditingId] = useState(null)
  const [editCaption, setEditCaption] = useState('')
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)
  const { confirm, showToast } = useUI()

  const load = async () => {
    setLoading(true)
    try {
      const q = filter === 'all' ? '' : `&status=${filter}`
      const r = await api.get(`/queue?page=${page}&limit=20${q}`)
      setPosts(r.data)
    } finally { setLoading(false) }
  }

  const requestApprove = (id) => {
    confirm({
      title: 'Approve Post?',
      message: 'Are you sure you want to approve this post for scheduled publishing?',
      type: 'success',
      onConfirm: async () => {
        try {
          await api.put(`/queue/${id}/approve`)
          showToast('Post approved successfully')
          load()
        } catch (e) {
          showToast('Failed to approve post', 'error')
        }
      }
    })
  }

  const requestReject = (id) => {
    confirm({
      title: 'Reject Post?',
      message: 'Are you sure you want to permanently reject and delete this post?',
      type: 'danger',
      onConfirm: async () => {
        try {
          await api.put(`/queue/${id}/reject`)
          showToast('Post rejected and deleted')
          load()
        } catch (e) {
          showToast('Failed to reject post', 'error')
        }
      }
    })
  }

  const requestPublishNow = (id) => {
    confirm({
      title: 'Publish Now?',
      message: 'Are you sure you want to instantly publish this post to Facebook right now?',
      type: 'primary',
      onConfirm: async () => {
        try {
          const { data } = await api.post(`/queue/${id}/publish-now`)
          if (data.dry_run) {
            showToast('[DRY-RUN] Simulation successful — article marked as posted.', 'success')
          } else {
            showToast('Successfully published to Facebook!', 'success')
          }
          load()
        } catch (e) {
          showToast('Publishing failed. Check logs.', 'error')
        }
      }
    })
  }

  const saveCaption = async (id) => {
    try {
      await api.put(`/queue/${id}`, { caption: editCaption })
      showToast('Caption updated')
      setEditingId(null)
      load()
    } catch (e) {
      showToast('Failed to update caption', 'error')
    }
  }

  useEffect(() => { load() }, [filter, page])

  return (
    <div className="fade-in">
      {/* Controls row: Filters + Refresh */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, marginTop: -8 }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {STATUS_FILTERS.map(s => (
            <button key={s} className={`btn btn-sm ${filter === s ? 'btn-primary' : 'btn-secondary'}`} onClick={() => { setFilter(s); setPage(1) }}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
        <button className="btn btn-secondary btn-sm" onClick={load} style={{ background: 'rgba(255,255,255,0.05)', borderRadius: 6 }}>
          Refresh
        </button>
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
    </div>
  )
}
