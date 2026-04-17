import { useEffect, useState } from 'react'
import PostCard from '../components/PostCard'
import api from '../lib/api'

export default function History() {
  const [posts, setPosts] = useState([])
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const r = await api.get(`/posts?page=${page}&limit=20`)
      setPosts(r.data)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [page])

  return (
    <div className="fade-in">
      <div className="page-header">
        <div>
          <h1 className="page-title">History</h1>
          <p className="page-subtitle">All published posts</p>
        </div>
        <button className="btn btn-secondary" onClick={load}>Refresh</button>
      </div>

      {loading && <div style={{ display: 'flex', justifyContent: 'center', padding: 32 }}><div className="spinner" /></div>}

      {!loading && posts.length === 0 && (
        <div className="card"><div className="empty-state">No posts published yet.</div></div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {posts.map(post => (
          <PostCard key={post.id} post={post} />
        ))}
      </div>

      {(page > 1 || posts.length === 20) && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 32 }}>
          {page > 1 && <button className="btn btn-secondary" onClick={() => setPage(p => p - 1)}>← Prev</button>}
          {posts.length === 20 && <button className="btn btn-secondary" onClick={() => setPage(p => p + 1)}>Next →</button>}
        </div>
      )}
    </div>
  )
}
