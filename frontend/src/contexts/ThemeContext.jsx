import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const THEME_KEY = 'neurodebug_theme'

const ThemeContext = createContext({
  theme: 'light',
  toggleTheme: () => {},
  setTheme: () => {},
})

export const useTheme = () => useContext(ThemeContext)

export const ThemeProvider = ({ children }) => {
  const [theme, setThemeState] = useState(() => {
    try {
      const saved = localStorage.getItem(THEME_KEY)
      return saved || 'light'
    } catch {
      return 'light'
    }
  })

  const applyTheme = useCallback((themeValue) => {
    const root = document.documentElement
    root.setAttribute('data-theme', themeValue)
    
    // Update CSS custom properties for smooth transitions
    root.style.setProperty('--theme-transition', 'background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease')
  }, [])

  const setTheme = useCallback((newTheme) => {
    setThemeState(newTheme)
    try {
      localStorage.setItem(THEME_KEY, newTheme)
    } catch {
      // Silently fail if localStorage is not available
    }
    applyTheme(newTheme)
  }, [applyTheme])

  const toggleTheme = useCallback(() => {
    setTheme(theme === 'light' ? 'dark' : 'light')
  }, [theme, setTheme])

  // Apply theme on mount and when theme changes
  useEffect(() => {
    applyTheme(theme)
  }, [theme, applyTheme])

  // Prevent flash of incorrect theme on page load
  useEffect(() => {
    // Remove the transition temporarily to prevent flash
    const root = document.documentElement
    root.style.setProperty('--theme-transition', 'none')
    
    // Apply the theme immediately
    applyTheme(theme)
    
    // Re-enable transitions after a short delay
    const timer = setTimeout(() => {
      root.style.setProperty('--theme-transition', 'background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease')
    }, 100)
    
    return () => clearTimeout(timer)
  }, [])

  const value = {
    theme,
    toggleTheme,
    setTheme,
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}
