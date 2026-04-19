import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import { UIProvider } from './context/UIContext'
import ToastContainer from './components/ToastContainer'
import ConfirmModal from './components/ConfirmModal'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Dashboard from './pages/Dashboard'
import Sources from './pages/Sources'
import Queue from './pages/Queue'
import History from './pages/History'
import Settings from './pages/Settings'
import DailyPost from './pages/DailyPost'
import CustomPost from './pages/CustomPost'
import Login from './pages/Login'

function PrivateLayout({ children }) {
  const token = localStorage.getItem('token')
  if (!token) return <Navigate to="/login" replace />
  return (
    <div className="app-layout">
      <Navbar />
      <main className="main-content" style={{ display: 'flex', flexDirection: 'column' }}>
        <div style={{ 
          maxWidth: 1200, margin: '0 auto', width: '100%', 
          flex: 1, display: 'flex', flexDirection: 'column' 
        }}>
          <div style={{ flex: 1 }}>{children}</div>
          <Footer />
        </div>
      </main>
    </div>
  )
}

export default function App() {
  return (
    <UIProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<PrivateLayout><Dashboard /></PrivateLayout>} />
          <Route path="/sources" element={<PrivateLayout><Sources /></PrivateLayout>} />
          <Route path="/queue" element={<PrivateLayout><Queue /></PrivateLayout>} />
          <Route path="/history" element={<PrivateLayout><History /></PrivateLayout>} />
          <Route path="/settings" element={<PrivateLayout><Settings /></PrivateLayout>} />
          <Route path="/daily-post" element={<PrivateLayout><DailyPost /></PrivateLayout>} />
          <Route path="/custom-post" element={<PrivateLayout><CustomPost /></PrivateLayout>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      <ToastContainer />
      <ConfirmModal />
    </UIProvider>
  )
}

