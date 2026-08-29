import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Activity, ArrowRight, ShieldCheck, Lock, Mail, User } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function Auth({ mode = 'login' }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const { login, register } = useAuth()

  const isRegister = mode === 'register'

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (isRegister) {
        const res = await register(email, password, name)
        if (res.success) {
          navigate('/dashboard')
        } else {
          setError(res.error || 'Registration failed')
        }
      } else {
        const res = await login(email, password)
        if (res.success) {
          navigate('/dashboard')
        } else {
          setError(res.error || 'Invalid email or password')
        }
      }
    } catch (err) {
      console.error('Auth submit error:', err)
      setError(err.message || 'Authentication error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--ink)] flex flex-col justify-center items-center px-6 py-12 font-display selection:bg-[var(--green)]/20 selection:text-[var(--green)]">
      <Link to="/" className="flex items-center gap-2.5 mb-8 group">
        <div className="w-9 h-9 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] flex items-center justify-center group-hover:border-[var(--border-strong)] transition-colors">
          <Activity className="w-5 h-5 text-[var(--ink)]" />
        </div>
        <span className="font-display font-bold text-xl tracking-tight text-[var(--ink)]">
          NeuroDebug
        </span>
      </Link>

      <div className="w-full max-w-md card-hover rounded-xl p-8 border border-[var(--line)]">
        <div className="text-center mb-6">
          <h1 className="font-display font-bold text-2xl text-[var(--ink)] tracking-tight">
            {isRegister ? 'Create your workspace' : 'Welcome back'}
          </h1>
          <p className="text-xs font-mono text-[var(--dim)] mt-1.5">
            {isRegister
              ? 'Get 5 free verification requests daily with project history'
              : 'Sign in to access your projects and verification audit logs'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-[var(--red)]/10 border border-[var(--red)]/30 text-xs font-mono text-[var(--red)]">
            ✕ {typeof error === 'string' ? error : JSON.stringify(error)}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {isRegister && (
            <div>
              <label className="block text-xs font-mono text-[var(--dim)] mb-1">
                Display Name
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Your Name"
                  required
                  className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--border-strong)]"
                />
                <User className="w-4 h-4 text-[var(--dim)] absolute left-3 top-3" />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-mono text-[var(--dim)] mb-1">
              Email Address
            </label>
            <div className="relative">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@example.com"
                required
                className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--border-strong)]"
              />
              <Mail className="w-4 h-4 text-[var(--dim)] absolute left-3 top-3" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono text-[var(--dim)] mb-1">
              Password
            </label>
            <div className="relative">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                className="w-full pl-9 pr-3 py-2.5 rounded-lg bg-[var(--surface-2)] border border-[var(--line)] text-xs font-mono text-[var(--ink)] focus:outline-none focus:border-[var(--border-strong)]"
              />
              <Lock className="w-4 h-4 text-[var(--dim)] absolute left-3 top-3" />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 rounded-lg bg-[var(--ink)] text-[var(--bg)] font-display font-bold text-xs hover:bg-white transition-all duration-150 flex items-center justify-center gap-2"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-[var(--bg)] border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <span>{isRegister ? 'Create Account' : 'Sign In'}</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-[var(--line)] text-center text-xs font-mono text-[var(--dim)]">
          {isRegister ? (
            <span>
              Already have an account?{' '}
              <Link to="/login" className="text-[var(--ink)] hover:underline font-semibold">
                Sign in
              </Link>
            </span>
          ) : (
            <span>
              New to NeuroDebug?{' '}
              <Link to="/register" className="text-[var(--ink)] hover:underline font-semibold">
                Create an account
              </Link>
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
