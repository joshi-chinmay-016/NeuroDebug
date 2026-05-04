import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import BlurText from './BlurText'
import SplashCursor from './SplashCursorNew'
import SaasFooter from './SaasFooter'
import StarBorder from './StarBorder'
import Galaxy from './Galaxy'
import TextType from './TextType'
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
      <div className="galaxy-background">
        <Galaxy 
          mouseRepulsion={true}
          mouseInteraction={true}
          density={1.5}
          glowIntensity={0.5}
          saturation={0.8}
          hueShift={240}
          transparent={true}
          speed={0.8}
          rotationSpeed={0.05}
        />
      </div>
      <SplashCursor 
          DENSITY_DISSIPATION={2}
          VELOCITY_DISSIPATION={3}
          PRESSURE={0.2}
          CURL={25}
          COLOR="#44ef58"
          SIM_RESOLUTION={64}
          DYE_RESOLUTION={1024}
          SPLAT_RADIUS={0.15}
          SPLAT_FORCE={4000}
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
          <div className="welcome-text">
            <TextType 
              text="Welcome to "
              typingSpeed={75}
              pauseDuration={1900}
              showCursor={true}
              cursorCharacter="|"
              deletingSpeed={40}
              loop={false}
              initialDelay={500}
              className="welcome-typing"
            />
          </div>
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
        <StarBorder
          as="div"
          className={`developer-card ${showDeveloperCard ? 'visible' : ''}`}
          color="#00ff88"
          speed="8s"
          thickness={3}
        >
          <h2 className="card-title">Meet the Developer</h2>
          <div className="developer-info">
            <h3 className="developer-name">Chinmay Joshi</h3>
            <p className="developer-role">FullStack Developer</p>
            <div className="developer-bio">
              <p>
                Passionate full-stack developer and AI enthusiast with a strong interest in building innovative, scalable, and user-centric digital solutions. Experienced in combining modern technologies, problem-solving skills, and creative thinking to develop impactful projects that address real-world challenges.
              </p>
            </div>
            <div className="developer-buttons">
              <a 
                href="https://github.com/joshi-chinmay-016" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-github"
              >
                <span className="btn-icon">🐙</span>
                Github
              </a>
              <a 
                href="https://www.linkedin.com/in/chinmay-joshi-59a840312/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="btn btn-linkedin"
              >
                <span className="btn-icon">💼</span>
                LinkedIn
              </a>
            </div>
          </div>
        </StarBorder>
      </section>

      <SaasFooter />

      <style jsx>{`
        .landing-page {
          min-height: 100vh;
          position: relative;
          overflow-x: hidden;
          background: #000000;
        }

        .galaxy-background {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: 0;
          pointer-events: none;
        }

        .splash-cursor-container {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          z-index: 100;
          pointer-events: none;
        }

        .hero-section {
          height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          background: radial-gradient(circle at center, #0a0a0a 0%, #000000 100%);
          z-index: 1;
        }

        .hero-content {
          text-align: center;
          z-index: 10;
          position: relative;
        }

        .welcome-text {
          margin-bottom: 1rem;
          text-align: center;
        }

        .welcome-typing {
          font-size: clamp(1.5rem, 4vw, 2.5rem);
          font-weight: 300;
          color: #ffffff;
          letter-spacing: 0.1em;
          text-shadow: 0 0 20px rgba(255, 255, 255, 0.3);
        }

        .hero-title {
          font-size: clamp(3rem, 10vw, 8rem);
          font-weight: 800;
          color: #ffffff;
          text-transform: uppercase;
          letter-spacing: -0.02em;
          line-height: 1;
          text-shadow: 0 0 40px rgba(255, 255, 255, 0.3);
        }

        .top-debug-button {
          position: fixed;
          top: 2rem;
          right: 2rem;
          z-index: 1000;
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
          position: relative;
          z-index: 1;
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
          margin-bottom: 1.5rem;
        }

        .developer-bio {
          margin-bottom: 2rem;
          text-align: left;
        }

        .developer-bio p {
          font-size: 0.95rem;
          line-height: 1.6;
          color: #cccccc;
          margin: 0;
        }

        .developer-buttons {
          display: flex;
          gap: 1rem;
          justify-content: center;
          flex-wrap: wrap;
        }

        .btn-github {
          background: #333333;
          color: #ffffff;
          padding: 8px 16px;
          border-radius: 8px;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-size: 0.9rem;
          font-weight: 500;
          transition: all 0.2s ease;
          border: 1px solid #444444;
          cursor: pointer;
        }

        .btn-github:hover {
          background: #444444;
          border-color: #666666;
          transform: translateY(-2px);
        }

        .btn-linkedin {
          background: #0077b5;
          color: #ffffff;
          padding: 8px 16px;
          border-radius: 8px;
          text-decoration: none;
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-size: 0.9rem;
          font-weight: 500;
          transition: all 0.2s ease;
          border: 1px solid #0077b5;
          cursor: pointer;
        }

        .btn-linkedin:hover {
          background: #005885;
          border-color: #004471;
          transform: translateY(-2px);
        }

        .btn-github:focus,
        .btn-linkedin:focus {
          outline: 2px solid #00ff88;
          outline-offset: 2px;
          position: relative;
          z-index: 10;
        }

        .btn-icon {
          font-size: 1rem;
        }

        .footer-images {
          display: flex;
          justify-content: center;
          gap: 2rem;
          margin-bottom: 1.5rem;
        }

        .footer-image {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          object-fit: cover;
          border: 2px solid #333333;
          transition: transform 0.3s ease;
        }

        .footer-image:hover {
          transform: scale(1.1);
          border-color: #00ff88;
        }

        .future-content {
          min-height: 100px;
          border: 2px dashed #333333;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          
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
