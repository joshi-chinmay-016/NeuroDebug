import { useTheme } from '../contexts/ThemeContext'

export default function SaasFooter() {
  const { theme } = useTheme()

  return (
    <>
      <footer className="saas-footer">
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
                  <li><a href="/debugger" className="footer-link">Debugger</a></li>
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

      <style jsx>{`
        .saas-footer {
          background: ${theme === 'dark' ? '#0a0a0a' : '#f8f9fa'};
          border-top: 1px solid ${theme === 'dark' ? '#333333' : '#e1e4e8'};
          padding: 3rem 0 2rem;
          margin-top: auto;
        }

        .footer-container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 0 2rem;
          display: flex;
          flex-direction: column;
          gap: 0;
        }

        /* ── Top: brand left, links right ── */
        .footer-top {
          display: flex;
          align-items: flex-start;
          gap: 4rem;
          padding-bottom: 2.5rem;
        }

        .footer-brand {
          flex: 0 0 240px;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .footer-logo {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .logo-icon {
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, #00ff88, #00cc66);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
        }

        .logo-text {
          font-size: 1.5rem;
          font-weight: 700;
          color: ${theme === 'dark' ? '#ffffff' : '#1a1a1a'};
        }

        .footer-tagline {
          color: ${theme === 'dark' ? '#888888' : '#666666'};
          font-size: 0.85rem;
          margin: 0;
          line-height: 1.5;
        }

        /* ── Link columns ── */
        .footer-links {
          flex: 1;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 2rem;
        }

        .footer-column-title {
          font-size: 0.75rem;
          font-weight: 600;
          color: ${theme === 'dark' ? '#ffffff' : '#1a1a1a'};
          margin: 0 0 1rem 0;
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }

        .footer-column-links {
          list-style: none;
          padding: 0;
          margin: 0;
          display: flex;
          flex-direction: column;
          gap: 0.6rem;
        }

        .footer-link {
          color: ${theme === 'dark' ? '#888888' : '#666666'};
          text-decoration: none;
          font-size: 0.875rem;
          transition: color 0.2s ease;
        }

        .footer-link:hover {
          color: #00ff88;
        }

        /* ── Bottom bar ── */
        .footer-bottom {
          border-top: 1px solid ${theme === 'dark' ? '#222222' : '#e1e4e8'};
          padding-top: 1.5rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .footer-contact {
          display: flex;
          align-items: center;
          gap: 2rem;
        }

        .contact-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .contact-icon {
          font-size: 1rem;
        }

        .contact-link {
          color: ${theme === 'dark' ? '#888888' : '#666666'};
          text-decoration: none;
          font-size: 0.875rem;
          transition: color 0.2s ease;
        }

        .contact-link:hover {
          color: #00ff88;
        }

        .footer-copyright {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .footer-copyright p {
          color: ${theme === 'dark' ? '#555555' : '#999999'};
          font-size: 0.8rem;
          margin: 0;
          white-space: nowrap;
        }

        .footer-badges {
          display: flex;
          gap: 0.5rem;
          align-items: center;
        }

        .badge {
          background: ${theme === 'dark' ? '#1a1a1a' : '#e8f5e9'};
          color: ${theme === 'dark' ? '#00ff88' : '#00cc66'};
          border: 1px solid ${theme === 'dark' ? '#2a2a2a' : '#c8e6c9'};
          padding: 0.2rem 0.6rem;
          border-radius: 4px;
          font-size: 0.72rem;
          font-weight: 500;
          white-space: nowrap;
        }

        /* ── Responsive ── */
        @media (max-width: 768px) {
          .footer-top {
            flex-direction: column;
            gap: 2rem;
          }

          .footer-brand {
            flex: none;
          }

          .footer-links {
            grid-template-columns: repeat(2, 1fr);
          }

          .footer-bottom {
            flex-direction: column;
            gap: 1.25rem;
            align-items: flex-start;
          }

          .footer-contact {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.75rem;
          }
        }

        @media (max-width: 480px) {
          .footer-links {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  )
}