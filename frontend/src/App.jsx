import { useState } from 'react'
import LoginPage from './components/LoginPage'
import Dashboard from './components/Dashboard'

export default function App() {
  const [session, setSession] = useState(() => {
    try {
      const saved = localStorage.getItem('kaznu_session')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  })

  const handleLogin = (data) => {
    localStorage.setItem('kaznu_session', JSON.stringify(data))
    setSession(data)
  }

  const handleLogout = () => {
    localStorage.removeItem('kaznu_session')
    setSession(null)
  }

  if (!session) {
    return <LoginPage onLogin={handleLogin} />
  }

  return <Dashboard session={session} onLogout={handleLogout} />
}
