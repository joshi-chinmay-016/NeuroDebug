import { Link, useLocation } from 'react-router-dom'
import { Brain, Zap, Settings, User, Menu, X, LogOut, ChevronDown } from 'lucide-react'
import { useState } from 'react'
import ThemeToggle from './ThemeToggle'
import { cn } from '../lib/utils'
import { useAuth } from '../contexts/AuthContext'

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const location = useLocation()
  const { isAuthenticated, user, logout } = useAuth()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard' },
    { name: 'Projects', href: '/projects' },
    { name: 'Debug', href: '/debug' },
    { name: 'History', href: '/history' },
    { name: 'Analytics', href: '/analytics' },
  ]

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center">
        <div className="mr-8 flex items-center gap-2">
          <Link to="/" className="flex items-center space-x-2 group">
            <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary via-purple-500 to-accent transition-all duration-300 group-hover:scale-110 group-hover:shadow-lg group-hover:shadow-primary/25">
              <Brain className="h-5 w-5 text-white" />
            </div>
            <span className="text-lg font-bold bg-gradient-to-r from-primary via-purple-500 to-accent bg-clip-text text-transparent transition-all duration-300 group-hover:opacity-90">
              NeuroDebug
            </span>
          </Link>
        </div>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          {navigation.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={cn(
                "relative px-4 py-2 text-sm font-medium transition-all duration-200 rounded-lg",
                location.pathname === item.href
                  ? "text-primary bg-primary/10"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
              )}
            >
              {item.name}
              {location.pathname === item.href && (
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 w-8 bg-gradient-to-r from-primary to-accent rounded-full" />
              )}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex items-center space-x-2">
          <ThemeToggle />
          
          {isAuthenticated ? (
            <>
              <Link
                to="/settings"
                className="hidden md:flex items-center space-x-2 px-3 py-2 text-sm font-medium text-muted-foreground transition-all duration-200 rounded-lg hover:text-foreground hover:bg-accent/50"
              >
                <Settings className="h-4 w-4" />
                <span>Settings</span>
              </Link>

              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-muted-foreground transition-all duration-200 rounded-lg hover:text-foreground hover:bg-accent/50"
                >
                  <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center text-white font-semibold">
                    {user?.display_name?.[0] || user?.email?.[0] || 'U'}
                  </div>
                  <ChevronDown className="h-4 w-4 transition-transform duration-200" style={{ transform: userMenuOpen ? 'rotate(180deg)' : 'none' }} />
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 rounded-xl border border-border/40 bg-card shadow-xl py-2 z-50">
                    <div className="px-4 py-2 border-b border-border/40">
                      <p className="text-sm font-medium">{user?.display_name || 'User'}</p>
                      <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                    </div>
                    <Link
                      to="/settings"
                      className="block px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
                      onClick={() => setUserMenuOpen(false)}
                    >
                      Settings
                    </Link>
                    <button
                      onClick={() => {
                        logout()
                        setUserMenuOpen(false)
                      }}
                      className="w-full text-left px-4 py-2 text-sm text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors flex items-center gap-2"
                    >
                      <LogOut className="h-4 w-4" />
                      Sign out
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="hidden md:inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all duration-200 border border-border/40 hover:bg-accent/50 h-9 px-4"
              >
                Sign in
              </Link>
              <Link
                to="/register"
                className="hidden md:inline-flex items-center justify-center rounded-lg text-sm font-medium transition-all duration-200 bg-gradient-to-r from-primary to-accent text-white hover:shadow-lg hover:shadow-primary/25 h-9 px-4"
              >
                Get Started
              </Link>
            </>
          )}

          {/* Mobile menu button */}
          <button
            type="button"
            className="md:hidden inline-flex items-center justify-center rounded-lg p-2 text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Navigation */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-border/40 bg-background/95 backdrop-blur-xl">
          <div className="container py-4 space-y-1">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  "block px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200",
                  location.pathname === item.href
                    ? "text-primary bg-primary/10"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/50"
                )}
                onClick={() => setMobileMenuOpen(false)}
              >
                {item.name}
              </Link>
            ))}
            {isAuthenticated ? (
              <>
                <Link
                  to="/settings"
                  className="block px-4 py-3 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent/50 rounded-lg transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Settings
                </Link>
                <button
                  onClick={() => {
                    logout()
                    setMobileMenuOpen(false)
                  }}
                  className="w-full text-left px-4 py-3 text-sm font-medium text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-colors flex items-center gap-2"
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="block px-4 py-3 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-accent/50 rounded-lg transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Sign in
                </Link>
                <Link
                  to="/register"
                  className="block px-4 py-3 text-sm font-medium bg-gradient-to-r from-primary to-accent text-white rounded-lg transition-all duration-200 text-center"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  )
}
