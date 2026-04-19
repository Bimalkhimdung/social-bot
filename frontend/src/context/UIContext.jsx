import { createContext, useContext, useState, useCallback } from 'react'

const UIContext = createContext()

export function UIProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const [confirmState, setConfirmState] = useState(null)

  const showToast = useCallback((message, type = 'success') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 4000)
  }, [])

  const confirm = useCallback(({ title, message, type = 'primary', onConfirm }) => {
    setConfirmState({ title, message, type, onConfirm })
  }, [])

  const closeConfirm = () => setConfirmState(null)

  return (
    <UIContext.Provider value={{ showToast, confirm, toasts, confirmState, closeConfirm }}>
      {children}
    </UIContext.Provider>
  )
}

export const useUI = () => {
  const context = useContext(UIContext)
  if (!context) throw new Error('useUI must be used within a UIProvider')
  return context
}
