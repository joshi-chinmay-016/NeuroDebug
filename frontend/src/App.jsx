import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext'
import { AuthProvider } from './contexts/AuthContext'
import { NotificationProvider } from './contexts/NotificationContext'
import Layout from './components/Layout'
import LandingPageNew from './components/LandingPageNew'
import Dashboard from './components/Dashboard'
import DebuggerNew from './components/DebuggerNew'
import Projects from './components/Projects'
import History from './components/History'
import Analytics from './components/Analytics'
import Pricing from './components/Pricing'
import Settings from './components/Settings'
import Auth from './components/Auth'
import CommandPalette from './components/CommandPalette'
import './index-modern.css'

function AppContent() {
  return (
    <Router>
      <CommandPalette />
      <Routes>
        {/* Landing Page */}
        <Route path="/" element={<LandingPageNew />} />

        {/* Auth Routes */}
        <Route path="/login" element={<Auth mode="login" />} />
        <Route path="/register" element={<Auth mode="register" />} />

        {/* Internal Developer Workspace with Persistent Shell */}
        <Route element={<Layout />}>
          <Route path="/debug" element={<DebuggerNew />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/projects" element={<Projects />} />
          <Route path="/history" element={<History />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/pricing" element={<Pricing />} />
          <Route path="/settings" element={<Settings />} />
        </Route>

        {/* Catch-all fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
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
