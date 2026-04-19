import { useUI } from '../context/UIContext'
import { CheckCircle, AlertCircle, X } from 'lucide-react'

export default function ToastContainer() {
  const { toasts } = useUI()

  return (
    <div className="toast-container">
      {toasts.map(toast => (
        <div 
          key={toast.id} 
          className={`toast toast-${toast.type} fade-in`}
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 12, 
            minWidth: 280,
            animation: 'slideInRight 0.3s ease-out'
          }}
        >
          <div style={{ color: toast.type === 'error' ? 'var(--red)' : '#10b981' }}>
            {toast.type === 'error' ? <AlertCircle size={18} /> : <CheckCircle size={18} />}
          </div>
          <div style={{ flex: 1, fontWeight: 500 }}>{toast.message}</div>
        </div>
      ))}
    </div>
  )
}
