import { useTheme } from './ThemeProvider'

export default function ThemeToggle({ className = '' }) {
  const { theme, toggleTheme } = useTheme()
  const nextTheme = theme === 'dark' ? 'light' : 'dark'
  const buttonClassName = ['theme-toggle', theme === 'dark' ? 'is-dark' : 'is-light', className]
    .filter(Boolean)
    .join(' ')

  return (
    <button
      type="button"
      className={buttonClassName}
      onClick={toggleTheme}
      aria-label={`Switch to ${nextTheme} mode`}
      aria-pressed={theme === 'dark'}
      title={`Theme: ${theme}. Activate to switch to ${nextTheme} mode.`}
    >
      <span className="theme-toggle-copy">
        <span className="theme-toggle-label">Theme</span>
        <span className="theme-toggle-value">{theme === 'dark' ? 'Dark' : 'Light'}</span>
      </span>
      <span className="theme-toggle-track" aria-hidden="true">
        <span className="theme-toggle-thumb" />
      </span>
    </button>
  )
}
