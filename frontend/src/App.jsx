import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import LandingPage from './components/LandingPage'
import Debugger from './components/Debugger'
import Dashboard from './components/Dashboard'
import Projects from './components/Projects'
import History from './components/History'
import Analytics from './components/Analytics'
import Pricing from './components/Pricing'
import Settings from './components/Settings'
import Layout from './components/Layout'
import './index-modern.css'

// Import Firebase test for development
if (import.meta.env.DEV) {
  import('./firebase-test.js')
}

// ── App ───────────────────────────────────────────────────────────
function AppContent() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/debug" element={<Debugger />} />
        <Route path="/debugger" element={<Debugger />} />
        
        {/* Protected Routes with Layout */}
        <Route path="/" element={<Layout />}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="history" element={<History />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="pricing" element={<Pricing />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  )
}
