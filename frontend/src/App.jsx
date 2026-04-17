import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import Sources from './pages/Sources'
import Queue from './pages/Queue'
import History from './pages/History'
import Settings from './pages/Settings'
import Logs from './pages/Logs'
import Login from './pages/Login'

function PrivateLayout({ children }) {
  const token = localStorage.getItem('token')
  if (!token) return <Navigate to="/login" replace />
  return (
    <div className="app-layout">
      <Navbar />
      <main className="main-content">{children}</main>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateLayout><Dashboard /></PrivateLayout>} />
        <Route path="/sources" element={<PrivateLayout><Sources /></PrivateLayout>} />
        <Route path="/queue" element={<PrivateLayout><Queue /></PrivateLayout>} />
        <Route path="/history" element={<PrivateLayout><History /></PrivateLayout>} />
        <Route path="/settings" element={<PrivateLayout><Settings /></PrivateLayout>} />
        <Route path="/logs" element={<PrivateLayout><Logs /></PrivateLayout>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
