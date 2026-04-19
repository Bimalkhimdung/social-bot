import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react'
import { useUI } from '../context/UIContext'

export default function ConfirmModal() {
  const { confirmState, closeConfirm } = useUI()

  if (!confirmState) return null

  const { title, message, type, onConfirm } = confirmState

  const getIcon = () => {
    switch (type) {
      case 'danger': return <XCircle size={28} />
      case 'success': return <CheckCircle size={28} />
      default: return <AlertTriangle size={28} />
    }
  }

  const getAccentColor = () => {
    switch (type) {
      case 'danger': return 'var(--red)'
      case 'success': return '#10b981'
      default: return 'var(--blue)'
    }
  }

  const handleConfirm = () => {
    onConfirm()
    closeConfirm()
  }

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      backgroundColor: 'rgba(5, 7, 10, 0.8)', backdropFilter: 'blur(8px)',
      zIndex: 10000, display: 'flex', alignItems: 'center', justifyContent: 'center'
    }} onClick={closeConfirm}>
      <div 
        className="card fade-in" 
        style={{ 
          width: 420, maxWidth: '90%', padding: '40px 32px', 
          textAlign: 'center', display: 'flex', flexDirection: 'column', 
          alignItems: 'center', boxShadow: '0 24px 48px rgba(0,0,0,0.4)',
          border: '1px solid rgba(255,255,255,0.08)'
        }} 
        onClick={e => e.stopPropagation()}
      >
        <div style={{ 
          width: 56, height: 56, borderRadius: '16px', marginBottom: 20, 
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          backgroundColor: `${getAccentColor()}15`,
          color: getAccentColor()
        }}>
          {getIcon()}
        </div>
        
        <h2 style={{ marginBottom: 12, fontSize: '1.5rem', fontWeight: 800, color: '#fff' }}>
          {title || 'Are you sure?'}
        </h2>
        
        <p style={{ marginBottom: 32, color: 'var(--text-secondary)', lineHeight: 1.6, fontSize: '0.95rem' }}>
          {message}
        </p>

        <div style={{ display: 'flex', gap: 12, width: '100%' }}>
          <button className="btn btn-secondary" style={{ flex: 1, height: 44 }} onClick={closeConfirm}>
            Cancel
          </button>
          <button 
            className="btn" 
            style={{ 
              flex: 1, height: 44,
              backgroundColor: getAccentColor(), 
              color: '#fff',
              border: 'none',
              fontWeight: 700
            }}
            onClick={handleConfirm}
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  )
}
