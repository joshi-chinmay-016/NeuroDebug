import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import BlurText from './BlurText'
import SplashCursor from './SplashCursorNew'
import { useTheme } from '../contexts/ThemeContext'

export default function LandingPage() {
  const { theme } = useTheme()
  const [showDeveloperCard, setShowDeveloperCard] = useState(false)
  const developerCardRef = useRef(null)

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY
      const windowHeight = window.innerHeight
      
      // Show developer card after scrolling past the first section
      if (scrollY > windowHeight * 0.3) {
        setShowDeveloperCard(true)
      } else {
        setShowDeveloperCard(false)
      }
    }

    // Show card immediately for testing
    setShowDeveloperCard(true)
    
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleAnimationComplete = () => {
    console.log('Neuro-Debug animation completed!')
  }

  return (
    <div className="landing-page">
      <SplashCursor 
        DENSITY_DISSIPATION={3}
        VELOCITY_DISSIPATION={5}
        PRESSURE={0.4}
        CURL={33}
        COLOR="#44ef58"
      />
      
      {/* Top Right Debug Button */}
      <div className="top-debug-button">
        <Link to="/debugger" className="debug-button">
          Start Debugging
        </Link>
      </div>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <BlurText
            text="Neuro-Debug"
            delay={140}
            animateBy="letters"
            direction="bottom"
            onAnimationComplete={handleAnimationComplete}
            className="hero-title"
          />
        </div>
      </section>

      {/* Developer Card Section */}
      <section className="developer-section" ref={developerCardRef}>
        <div className={`developer-card ${showDeveloperCard ? 'visible' : ''}`}>
          <h2 className="card-title">Meet the Developer</h2>
          <div className="developer-info">
            <h3 className="developer-name">Chinmay Joshi</h3>
            <p className="developer-role">FullStack Developer</p>
            <div className="future-content">
              {/* Space for future content */}
            </div>
          </div>
        </div>
      </section>

      <style jsx>{`
        .landing-page {
          min-height: 100vh;
          position: relative;
          overflow-x: hidden;
          background: #000000;
        }

        .hero-section {
          height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          background: radial-gradient(circle at center, #0a0a0a 0%, #000000 100%);
        }

        .hero-content {
          text-align: center;
          z-index: 10;
          position: relative;
        }

        .hero-title {
          font-size: clamp(3rem, 10vw, 8rem);
          font-weight: 700;
          color: #ffffff;
          margin: 0;
          letter-spacing: -0.02em;
          line-height: 1;
          text-shadow: 0 0 40px rgba(0, 255, 136, 0.5);
        }

        .top-debug-button {
          position: fixed;
          top: 2rem;
          right: 2rem;
          z-index: 100;
        }

        .debug-button {
          display: inline-block;
          padding: 0.8rem 1.5rem;
          font-size: 1rem;
          font-weight: 600;
          color: #000000;
          background: #00ff88;
          border: none;
          border-radius: 6px;
          text-decoration: none;
          transition: all 0.3s ease;
          box-shadow: 0 4px 15px rgba(0, 255, 136, 0.4);
        }

        .debug-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(0, 255, 136, 0.6);
          background: #00ff99;
        }

        .developer-section {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 4rem 2rem;
          background: #000000;
          position: relative;
        }

        .developer-card {
          background: #000000;
          border: 2px solid #333333;
          border-radius: 16px;
          padding: 3rem;
          max-width: 500px;
          width: 100%;
          text-align: center;
          opacity: 0;
          transform: translateY(50px);
          transition: all 0.8s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
          position: relative;
          overflow: hidden;
        }

        .developer-card.visible {
          opacity: 1;
          transform: translateY(0);
        }

        .card-title {
          font-size: 2.5rem;
          font-weight: 600;
          color: #ffffff;
          margin-bottom: 1rem;
          letter-spacing: -0.01em;
        }

        .developer-name {
          font-size: 1.8rem;
          font-weight: 600;
          color: #ffffff;
          margin-bottom: 0.5rem;
          letter-spacing: -0.01em;
        }

        .developer-role {
          font-size: 1.2rem;
          color: #00ff88;
          margin-bottom: 2rem;
        }

        .future-content {
          min-height: 100px;
          border: 2px dashed #333333;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: #666666;
          font-style: italic;
          font-size: 0.9rem;
        }

        @media (max-width: 768px) {
          .hero-title {
            font-size: clamp(2.5rem, 8vw, 5rem);
          }
          
          .top-debug-button {
            top: 1rem;
            right: 1rem;
          }
          
          .debug-button {
            padding: 0.6rem 1.2rem;
            font-size: 0.9rem;
          }
          
          .developer-card {
            padding: 2rem;
            margin: 0 1rem;
          }
          
          .card-title {
            font-size: 1.5rem;
          }
          
          .developer-name {
            font-size: 1.25rem;
          }
        }
      `}</style>
    </div>
  )
}
