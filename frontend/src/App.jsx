import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import LandingPage from './components/LandingPage'
import Debugger from './components/Debugger'
import './index.css'

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
        <Route path="/debugger" element={<Debugger />} />
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
