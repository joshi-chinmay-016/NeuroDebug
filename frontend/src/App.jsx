import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import { NotificationProvider } from './contexts/NotificationContext'
import Header from './components/Header'
import Layout from './components/Layout'
import LandingPage from './components/LandingPage'
import Dashboard from './components/Dashboard'
import Debugger from './components/Debugger'
import Projects from './components/Projects'
import History from './components/History'
import Analytics from './components/Analytics'
import Settings from './components/Settings'
import Auth from './components/Auth'
import CommandPalette from './components/CommandPalette'
import './index-modern.css'

// Import Firebase test for development
if (import.meta.env.DEV) {
  import('./firebase-test.js')
}

// ── App ───────────────────────────────────────────────────────────
function AppContent() {
  return (
    <Router>
      <CommandPalette />
      <Routes>
        <Route path="/" element={<Debugger />} />
        <Route path="/landing" element={<LandingPage />} />
        <Route path="/login" element={<Auth mode="login" />} />
        <Route path="/register" element={<Auth mode="register" />} />
        <Route path="/debug" element={<Navigate to="/" replace />} />

        {/* Protected Routes with Layout */}
        <Route path="/" element={<Layout />}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="history" element={<History />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <NotificationProvider>
          <AppContent />
        </NotificationProvider>
      </AuthProvider>
    </ThemeProvider>
  )
}
