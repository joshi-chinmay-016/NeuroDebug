import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import BlurText from './BlurText'
import SplashCursor from './SplashCursorNew'
import SaasFooter from './SaasFooter'
import StarBorder from './StarBorder'
import TextType from './TextType'
// import NeuralNetworkBackground from './NeuralNetworkBackground' // Temporarily disabled due to rolldown bundler issue
import './LandingPage.css'

gsap.registerPlugin(ScrollTrigger)

export default function LandingPage() {
  const [showDeveloperCard, setShowDeveloperCard] = useState(true)
  const developerCardRef = useRef(null)
  const featuresRef = useRef(null)

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

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // GSAP animations for scroll
  useEffect(() => {
    const ctx = gsap.context(() => {
      // Animate feature cards on scroll
      gsap.from('.feature-card', {
        scrollTrigger: {
          trigger: '.features-section',
          start: 'top 80%',
          end: 'bottom 20%',
          scrub: 1,
        },
        y: 100,
        opacity: 0,
        stagger: 0.2,
        duration: 0.8,
      })

      // Animate developer card
      gsap.from('.developer-card', {
        scrollTrigger: {
          trigger: '.developer-card',
          start: 'top 85%',
        },
        y: 50,
        opacity: 0,
        duration: 1,
      })
    }, featuresRef)

    return () => ctx.revert()
  }, [])

  const handleAnimationComplete = () => {
    console.log('Neuro-Debug animation completed!')
  }

  return (
    <div className="landing-page">
      {/* NeuralNetworkBackground temporarily disabled due to rolldown bundler issue */}
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
          <h1 className="hero-title">
            <BlurText 
              text="NeuroDebug" 
              onAnimationComplete={handleAnimationComplete}
            />
          </h1>
          <div className="hero-subtitle">
            <TextType 
              text="AI-Powered Code Debugging"
              speed={50}
            />
          </div>
          <div className="hero-description">
            <p>
              Combine static AST analysis with dynamic LLM reasoning for 
              intelligent code debugging with verified fixes.
            </p>
          </div>
          <div className="hero-actions">
            <Link to="/debugger" className="btn btn-primary">
              Start Debugging
            </Link>
            <Link to="/dashboard" className="btn btn-secondary">
              View Dashboard
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section" ref={featuresRef}>
        <div className="section-container">
          <h2 className="section-title">Why NeuroDebug?</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🧠</div>
              <h3>Neuro-Symbolic Analysis</h3>
              <p>
                Combines deterministic AST parsing with neural LLM reasoning 
                for comprehensive error detection.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">✅</div>
              <h3>Verified Fixes</h3>
              <p>
                Every candidate patch is executed and tested before presentation, 
                ensuring reliable solutions.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3>Instant Feedback</h3>
              <p>
                Get real-time error detection, explanations, and fixes in seconds, 
                not minutes or hours.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🔒</div>
              <h3>Secure & Private</h3>
              <p>
                Your code never leaves your environment. All analysis happens locally 
                with optional cloud augmentation.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>Precision Targeting</h3>
              <p>
                AST-based analysis pinpoints exact error locations, reducing false 
                positives and improving accuracy.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Analytics Dashboard</h3>
              <p>
                Track your debugging history, success rates, and performance metrics 
                with comprehensive analytics.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Developer Card */}
      {showDeveloperCard && (
        <div className="developer-card" ref={developerCardRef}>
          <div className="developer-card-content">
            <StarBorder>
              <div className="developer-card-inner">
                <h3>Built by Developers, for Developers</h3>
                <p>
                  NeuroDebug was created to solve the fundamental problem of 
                  automated code debugging by combining the reliability of static 
                  analysis with the intelligence of large language models.
                </p>
                <div className="developer-card-actions">
                  <Link to="/about" className="btn btn-ghost">
                    Learn More
                  </Link>
                </div>
              </div>
            </StarBorder>
          </div>
        </div>
      )}

      {/* Footer */}
      <SaasFooter />
    </div>
  )
}
