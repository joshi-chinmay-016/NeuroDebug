import { useTheme } from '../contexts/ThemeContext'
import './SaasFooter.css'

export default function SaasFooter() {
  const { theme } = useTheme()

  return (
    <footer className={`saas-footer ${theme}`}>
      <div className="footer-container">

        {/* ── Top row: brand + links ── */}
        <div className="footer-top">

          <div className="footer-brand">
            <div className="footer-logo">
              <div className="logo-icon">🧠</div>
              <span className="logo-text">NeuroDebug</span>
            </div>
            <p className="footer-tagline">AI-Powered Code Debugging Solution</p>
          </div>

          <div className="footer-links">
            <div className="footer-column">
              <h4 className="footer-column-title">Product</h4>
              <ul className="footer-column-links">
                <li><a href="/dashboard" className="footer-link">Debugger</a></li>
                <li><a href="/" className="footer-link">Home</a></li>
              </ul>
            </div>

            <div className="footer-column">
              <h4 className="footer-column-title">Resources</h4>
              <ul className="footer-column-links">
                <li>
                  <a href="https://docs.neurodebug.com" className="footer-link" target="_blank" rel="noopener noreferrer">
                    Documentation
                  </a>
                </li>
                <li>
                  <a href="https://github.com/joshi-chinmay-016/neurodebug" className="footer-link" target="_blank" rel="noopener noreferrer">
                    GitHub
                  </a>
                </li>
              </ul>
            </div>

            <div className="footer-column">
              <h4 className="footer-column-title">Company</h4>
              <ul className="footer-column-links">
                <li><a href="/about" className="footer-link">About</a></li>
                <li><a href="/privacy" className="footer-link">Privacy</a></li>
                <li><a href="/terms" className="footer-link">Terms</a></li>
              </ul>
            </div>
          </div>

        </div>

        {/* ── Bottom row: contact + copyright — full width ── */}
        <div className="footer-bottom">
          <div className="footer-contact">
            <div className="contact-item">
              <span className="contact-icon">📧</span>
              <a href="mailto:joshichinmay3201@gmail.com" className="contact-link">
                joshichinmay3201@gmail.com
              </a>
            </div>
            <div className="contact-item">
              <span className="contact-icon">🐙</span>
              <a href="https://github.com/joshi-chinmay-016" className="contact-link" target="_blank" rel="noopener noreferrer">
                GitHub
              </a>
            </div>
          </div>

          <div className="footer-copyright">
            <p>&copy; {new Date().getFullYear()} NeuroDebug. All rights reserved.</p>
            <div className="footer-badges">
              <span className="badge">Built with ❤️</span>
              <span className="badge">AI-Powered</span>
            </div>
          </div>
        </div>

      </div>
    </footer>
  )
}
