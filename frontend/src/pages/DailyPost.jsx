import { useState, useEffect, useCallback } from 'react'
import { RefreshCw, Send, CheckCircle, AlertTriangle, Clock } from 'lucide-react'
import api from '../lib/api'
import { useUI } from '../context/UIContext'

export default function DailyPost() {
  const { showToast, confirm } = useUI()
  const [cardUrl, setCardUrl] = useState(null)
  const [loading, setLoading] = useState(true)
  const [posting, setPosting] = useState(false)
  const [lastResult, setLastResult] = useState(null)
  const [timestamp, setTimestamp] = useState(Date.now())

  const refreshCard = useCallback(() => {
    setLoading(true)
    setTimestamp(Date.now())
  }, [])

  useEffect(() => {
    // Build card URL with cache-busting timestamp
    setCardUrl(`/api/daily/preview-card?t=${timestamp}`)
  }, [timestamp])

  const handleImageLoad = () => setLoading(false)
  const handleImageError = () => {
    setLoading(false)
    showToast('Failed to load card preview. Is the backend running?', 'error')
  }

  const handlePostToFacebook = () => {
    confirm({
      title: 'Post Daily NEPSE Update?',
      message: "This will generate a live market card and publish it to your Facebook page right now. Continue?",
      type: 'primary',
      onConfirm: async () => {
        setPosting(true)
        setLastResult(null)
        try {
          const { data } = await api.post('/daily/post-now')
          setLastResult({ success: true, ...data })
          showToast(
            data.dry_run ? 'Posted (dry-run — FB not configured)' : `Posted to Facebook! ID: ${data.fb_post_id}`,
            data.dry_run ? 'warning' : 'success'
          )
          // Refresh the card preview after posting
          refreshCard()
        } catch (err) {
          const msg = err.response?.data?.detail || 'Failed to post. Check backend logs.'
          setLastResult({ success: false, message: msg })
          showToast(msg, 'error')
        } finally {
          setPosting(false)
        }
      },
    })
  }

  return (
    <div className="fade-in" style={{ paddingTop: 8 }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: 24, alignItems: 'start' }}>

        {/* Card Preview */}
        <div className="card" style={{ padding: 24 }}>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16,
          }}>
            <span style={{
              fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em',
              color: 'var(--text-muted)', textTransform: 'uppercase'
            }}>
              Card Preview
            </span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn btn-secondary btn-sm"
                onClick={refreshCard}
                disabled={loading}
                style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', padding: '6px 12px' }}
              >
                <RefreshCw size={13} style={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
                {loading ? 'Loading…' : 'Refresh'}
              </button>
              <button
                className="btn btn-primary btn-sm"
                onClick={handlePostToFacebook}
                disabled={posting || loading}
                style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', padding: '6px 14px' }}
              >
                <Send size={13} />
                {posting ? 'Posting…' : 'Post to Facebook'}
              </button>
            </div>
          </div>

          <div style={{
            background: 'var(--surface-2)',
            borderRadius: 12, overflow: 'hidden',
            border: '1px solid var(--border)',
            minHeight: 300,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            position: 'relative',
          }}>
            {loading && (
              <div style={{
                position: 'absolute', inset: 0,
                display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center', gap: 12,
                background: 'var(--surface-2)',
                zIndex: 1,
              }}>
                <RefreshCw size={28} style={{ animation: 'spin 1s linear infinite', color: 'var(--text-muted)' }} />
                <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>Generating card from live data…</span>
              </div>
            )}
            {cardUrl && (
              <img
                key={timestamp}
                src={cardUrl}
                alt="NEPSE Daily Card Preview"
                onLoad={handleImageLoad}
                onError={handleImageError}
                style={{
                  width: '100%',
                  display: 'block',
                  borderRadius: 12,
                  opacity: loading ? 0 : 1,
                  transition: 'opacity 0.3s ease',
                }}
              />
            )}
          </div>

          <p style={{ margin: '12px 0 0', fontSize: '0.78rem', color: 'var(--text-muted)', textAlign: 'center' }}>
            Data sourced from sharehubnepal.com · Date in Nepali (Bikram Sambat)
          </p>
        </div>

        {/* Side Panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Post Result */}
          {lastResult && (
            <div className="card" style={{
              padding: 20,
              border: `1px solid ${lastResult.success ? 'var(--green)' : 'var(--red)'}`,
              background: lastResult.success ? 'rgba(34,197,94,0.06)' : 'rgba(239,68,68,0.06)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                {lastResult.success
                  ? <CheckCircle size={18} color="var(--green)" />
                  : <AlertTriangle size={18} color="var(--red)" />}
                <span style={{ fontWeight: 700, color: lastResult.success ? 'var(--green)' : 'var(--red)' }}>
                  {lastResult.success ? 'Post Successful' : 'Post Failed'}
                </span>
              </div>
              {lastResult.success && (
                <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                  {lastResult.dry_run && (
                    <div style={{ color: 'var(--yellow)', marginBottom: 6 }}>
                      ⚠ Dry-run mode (FB not configured)
                    </div>
                  )}
                  {lastResult.date && <div>Date: <strong>{lastResult.date}</strong></div>}
                  {lastResult.fb_post_id && (
                    <div>Post ID: <code style={{ fontSize: '0.78rem' }}>{lastResult.fb_post_id}</code></div>
                  )}
                </div>
              )}
              {!lastResult.success && (
                <p style={{ margin: 0, fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                  {lastResult.message}
                </p>
              )}
            </div>
          )}

          {/* Info card */}
          <div className="card" style={{ padding: 20 }}>
            <div style={{
              fontSize: '0.75rem', fontWeight: 700, letterSpacing: '0.08em',
              color: 'var(--text-muted)', marginBottom: 14, textTransform: 'uppercase'
            }}>
              What this posts
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { label: 'NEPSE Index Point', desc: 'Current value + change %' },
                { label: 'Total Turnover', desc: 'In अर्ब / करोड format' },
                { label: 'Total Traded Shares', desc: 'In करोड / लाख format' },
                { label: 'Advanced / Declined', desc: 'Stock movement count' },
                { label: 'Nepali Date', desc: 'Bikram Sambat in Devanagari' },
              ].map(({ label, desc }) => (
                <div key={label} style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <span style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)' }}>{label}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{desc}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Schedule note */}
          <div className="card" style={{ padding: 16, background: 'rgba(99,102,241,0.07)', border: '1px solid rgba(99,102,241,0.2)' }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <Clock size={16} style={{ color: '#818cf8', flexShrink: 0, marginTop: 2 }} />
              <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                You can also schedule this to post automatically each day after market close via the <strong>Settings</strong> page (coming soon).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

