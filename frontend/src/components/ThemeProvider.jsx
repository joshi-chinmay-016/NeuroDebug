import { createContext, useContext, useLayoutEffect, useMemo, useState } from 'react'

export const THEME_STORAGE_KEY = 'neurodebug-theme'

const ThemeContext = createContext(null)
const VALID_THEMES = new Set(['light', 'dark'])

function getSystemTheme() {
  if (typeof window === 'undefined') {
    return 'dark'
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getInitialTheme() {
  if (typeof document !== 'undefined') {
    const documentTheme = document.documentElement.dataset.theme
    if (VALID_THEMES.has(documentTheme)) {
      return documentTheme
    }
  }

  if (typeof window !== 'undefined') {
    try {
      const storedTheme = window.localStorage.getItem(THEME_STORAGE_KEY)
      if (VALID_THEMES.has(storedTheme)) {
        return storedTheme
      }
    } catch (_) {}
  }

  return getSystemTheme()
}

function applyTheme(theme) {
  if (typeof document === 'undefined') {
    return
  }

  document.documentElement.dataset.theme = theme
  document.documentElement.style.colorScheme = theme
}

function persistTheme(theme) {
  if (typeof window === 'undefined') {
    return
  }

  try {
    window.localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch (_) {}
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(getInitialTheme)

  useLayoutEffect(() => {
    applyTheme(theme)
    persistTheme(theme)
  }, [theme])

  const setTheme = (nextTheme) => {
    setThemeState((currentTheme) => {
      const resolvedTheme =
        typeof nextTheme === 'function' ? nextTheme(currentTheme) : nextTheme

      return VALID_THEMES.has(resolvedTheme) ? resolvedTheme : currentTheme
    })
  }

  const value = useMemo(
    () => ({
      theme,
      isDark: theme === 'dark',
      setTheme,
      toggleTheme: () => setTheme((currentTheme) => (currentTheme === 'dark' ? 'light' : 'dark')),
    }),
    [theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)

  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }

  return context
}
