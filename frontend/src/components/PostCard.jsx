import { useState } from 'react'
import { ExternalLink, Image, Eye, X, Loader } from 'lucide-react'

const STATUS_COLORS = {
  pending:  'var(--amber)',
  approved: 'var(--blue)',
  posted:   'var(--green)',
  rejected: 'var(--red)',
}

// ── PostCard ──────────────────────────────────────────────────────────────────
export default function PostCard({ post, actions }) {
  const { article, status, caption, posted_at, scheduled_at } = post

  return (
    <div className="card fade-in" style={{ display: 'flex', flexDirection: 'column', padding: 16 }}>
      
      {/* Top Row: Info */}
      <div style={{ display: 'flex', gap: 16 }}>
        {/* Thumbnail */}
        <div style={{
          width: 90, height: 90, flexShrink: 0,
          borderRadius: 'var(--radius-sm)',
          overflow: 'hidden',
          background: 'var(--bg-elevated)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          {article?.image_url
            ? <img src={article.image_url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => { e.target.style.display='none' }} />
            : <Image size={28} color="var(--text-muted)" />
          }
        </div>

        {/* Content */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span className={`badge badge-${status}`}>{status}</span>
            {article?.source_label
              ? <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{article.source_label}</span>
              : article?.source_name && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{article.source_name}</span>
            }
          </div>

          <div style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {article?.title}
          </div>

          {caption && (
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', maxHeight: 48, overflow: 'hidden' }}>
              {caption}
            </div>
          )}

          {article?.article_url && (
            <a href={article.article_url} target="_blank" rel="noreferrer"
              style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: '0.75rem', color: 'var(--accent)', marginTop: 4 }}>
              <ExternalLink size={12} /> Read article
            </a>
          )}

          {article?.scraped_at && (
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
              <span style={{ opacity: 0.6 }}>Scraped:</span> 
              <span>{new Date(article.scraped_at).toLocaleString('en-US', { 
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false 
              })}</span>
            </div>
          )}

          {posted_at && (
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: 4 }}>
              Posted: {new Date(posted_at).toLocaleString()}
            </div>
          )}
          {scheduled_at && !posted_at && (
            <div style={{ fontSize: '0.75rem', color: 'var(--amber)', marginTop: 4 }}>
              Scheduled: {new Date(scheduled_at).toLocaleString()}
            </div>
          )}
        </div>
      </div>

      {/* Bottom Row: Actions */}
      <div style={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 10, marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
        {/* Preview Card button — opens safely in a fresh tab */}
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => window.open(`/api/queue/${post.id}/preview-card`, '_blank')}
          title="Preview the Facebook card image"
          style={{ display: 'flex', alignItems: 'center', gap: 5 }}
        >
          <Eye size={13} /> Preview Card
        </button>

        {/* Post-specific action buttons injected from Queue.jsx */}
        {actions}
      </div>
    </div>
  )
}
