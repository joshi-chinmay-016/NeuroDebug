import React, { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'

/**
 * VerificationCore3D
 * 
 * Central 3D centerpiece of the NeuroDebug landing page.
 * Implements a full motion & material scroll-driven state machine:
 *  - 0.00-0.20: Unresolved (Red #F2555A, chaotic high jitter amp, rapid tumbling wireframe)
 *  - 0.20-0.45: Candidate Patch (Amber #F2B84B, settling jitter, slower rotation)
 *  - 0.45-0.75: Executing (Amber, active scan ring sweeping up/down across surface)
 *  - 0.75-1.00: Verified (Green #3FE08A, jitter=0, solid faceted low-poly mesh, calm rotation, breathing outer glow)
 */
export default function VerificationCore3D({ onStateChange }) {
  const containerRef = useRef(null)
  const isHoveredRef = useRef(false)
  const pulseTriggerRef = useRef(false)
  const lastStageRef = useRef(-1)
  const scrollRef = useRef(0)

  const [hasWebGL, setHasWebGL] = useState(true)

  useEffect(() => {
    // 1. Passive scroll listener updating ref directly
    const updateScroll = () => {
      const doc = document.documentElement
      const totalScroll = doc.scrollHeight - window.innerHeight
      const current = window.scrollY || doc.scrollTop || 0
      const progress = totalScroll > 0 ? Math.max(0, Math.min(1, current / totalScroll)) : 0
      scrollRef.current = progress
    }

    updateScroll()
    window.addEventListener('scroll', updateScroll, { passive: true })

    const container = containerRef.current
    if (!container) return

    // WebGL context check
    try {
      const canvas = document.createElement('canvas')
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
      if (!gl) {
        setHasWebGL(false)
        return
      }
    } catch {
      setHasWebGL(false)
      return
    }

    const width = container.clientWidth || 500
    const height = container.clientHeight || 500

    // Scene, Camera, Renderer
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
    camera.position.z = 5.8

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance',
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    container.appendChild(renderer.domElement)

    // Base Color Palette
    const colorRed = new THREE.Color('#F2555A')
    const colorAmber = new THREE.Color('#F2B84B')
    const colorGreen = new THREE.Color('#3FE08A')

    // 1. Core Icosahedron Geometry (detail=2 for rich vertex displacement)
    const radius = 1.7
    const detail = 2
    const baseGeo = new THREE.IcosahedronGeometry(radius, detail)
    const posAttr = baseGeo.attributes.position
    const origPositions = new Float32Array(posAttr.array)

    // Wireframe Mesh (active in unresolved/candidate states)
    const wireGeo = baseGeo.clone()
    const wireMaterial = new THREE.MeshBasicMaterial({
      color: colorRed,
      wireframe: true,
      transparent: true,
      opacity: 0.95,
      depthWrite: false,
    })
    const wireMesh = new THREE.Mesh(wireGeo, wireMaterial)
    scene.add(wireMesh)

    // Solid Faceted Mesh (active in verified state)
    const solidGeo = baseGeo.clone()
    const solidMaterial = new THREE.MeshStandardMaterial({
      color: colorGreen,
      flatShading: true,
      roughness: 0.35,
      metalness: 0.25,
      transparent: true,
      opacity: 0.0,
      depthWrite: true,
    })
    const solidMesh = new THREE.Mesh(solidGeo, solidMaterial)
    solidMesh.visible = false
    scene.add(solidMesh)

    // Glow Outer Mesh (appears when approaching verified)
    const glowGeo = new THREE.IcosahedronGeometry(radius * 1.14, 1)
    const glowMaterial = new THREE.MeshBasicMaterial({
      color: colorGreen,
      wireframe: true,
      transparent: true,
      opacity: 0.0,
      depthWrite: false,
    })
    const glowMesh = new THREE.Mesh(glowGeo, glowMaterial)
    glowMesh.visible = false
    scene.add(glowMesh)

    // 2. Scan Ring (Execution pass representation)
    const ringGeo = new THREE.TorusGeometry(radius * 1.35, 0.025, 16, 64)
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: colorAmber,
      transparent: true,
      opacity: 0.0,
      depthWrite: false,
    })
    const scanRing = new THREE.Mesh(ringGeo, ringMaterial)
    scanRing.rotation.x = Math.PI / 3
    scanRing.visible = false
    scene.add(scanRing)

    // 3. One-off Click Pulse Ring Easter Egg
    const pulseRingGeo = new THREE.TorusGeometry(radius * 0.5, 0.035, 16, 64)
    const pulseRingMat = new THREE.MeshBasicMaterial({
      color: colorGreen,
      transparent: true,
      opacity: 0.0,
      depthWrite: false,
    })
    const pulseRing = new THREE.Mesh(pulseRingGeo, pulseRingMat)
    pulseRing.rotation.x = Math.PI / 4
    scene.add(pulseRing)

    // 4. Ambient Background Particles
    const particleCount = 220
    const particleGeo = new THREE.BufferGeometry()
    const particlePositions = new Float32Array(particleCount * 3)
    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePositions[i] = (Math.random() - 0.5) * 14
      particlePositions[i + 1] = (Math.random() - 0.5) * 14
      particlePositions[i + 2] = (Math.random() - 0.5) * 8 - 2
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3))
    const particleMaterial = new THREE.PointsMaterial({
      color: colorRed,
      size: 0.035,
      transparent: true,
      opacity: 0.25,
      depthWrite: false,
    })
    const particles = new THREE.Points(particleGeo, particleMaterial)
    scene.add(particles)

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.8)
    scene.add(ambientLight)
    const dirLight = new THREE.DirectionalLight(0xffffff, 1.4)
    dirLight.position.set(4, 5, 6)
    scene.add(dirLight)

    // Mouse Parallax & Interactions
    let mouseX = 0
    let mouseY = 0
    const handleMouseMove = (e) => {
      const rect = container.getBoundingClientRect()
      mouseX = ((e.clientX - rect.left) / rect.width - 0.5) * 2
      mouseY = -((e.clientY - rect.top) / rect.height - 0.5) * 2
    }
    const handleMouseEnter = () => { isHoveredRef.current = true }
    const handleMouseLeave = () => { isHoveredRef.current = false }
    const handleClick = () => {
      pulseTriggerRef.current = true
      pulseRing.scale.set(1, 1, 1)
      pulseRingMat.opacity = 0.85
    }

    container.addEventListener('mousemove', handleMouseMove)
    container.addEventListener('mouseenter', handleMouseEnter)
    container.addEventListener('mouseleave', handleMouseLeave)
    container.addEventListener('click', handleClick)

    const handleResize = () => {
      if (!container) return
      const w = container.clientWidth || 500
      const h = container.clientHeight || 500
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }
    window.addEventListener('resize', handleResize)

    // High-performance simplex-like noise
    const calcNoise = (x, y, z, t) => {
      return (
        Math.sin(x * 3.2 + t * 5.0) * Math.cos(y * 2.8 + t * 4.0) +
        Math.sin(z * 3.5 + t * 3.2) * 0.5 +
        Math.cos((x + y + z) * 2.0 + t * 6.0) * 0.3
      ) * 0.5
    }

    // Animation Loop
    let animId
    let time = 0
    let bootScale = 0
    const startTime = performance.now()

    const animate = () => {
      animId = requestAnimationFrame(animate)
      time += 0.018

      // 1. Initial Boot-up scale-in
      const elapsed = (performance.now() - startTime) / 1000
      if (elapsed < 1.2) {
        const t = elapsed / 1.2
        bootScale = Math.min(1.0, t < 0.7 ? t * 1.3 : 1.0 + Math.sin(t * Math.PI) * 0.08)
      } else {
        bootScale = 1.0
      }

      // 2. Read exact scroll progress from ref
      const p = Math.max(0, Math.min(1, scrollRef.current))

      // Motion & Material variables governed by scrollProgress `p`:
      const activeColor = new THREE.Color()
      let jitterAmp = 0.26
      let rotBaseSpeed = 0.016
      let stage = 0

      if (p < 0.20) {
        // [0.00 - 0.20]: UNRESOLVED
        // High chaotic jitter, rapid erratic rotation, wireframe only
        const t = p / 0.20
        activeColor.copy(colorRed)
        jitterAmp = THREE.MathUtils.lerp(0.26, 0.20, t)
        rotBaseSpeed = THREE.MathUtils.lerp(0.022, 0.016, t)

        wireMesh.visible = true
        wireMaterial.opacity = 0.95
        solidMesh.visible = false
        glowMesh.visible = false
        scanRing.visible = false
        stage = 0
      } else if (p < 0.45) {
        // [0.20 - 0.45]: CANDIDATE PATCH
        // Color lerps Red -> Amber, jitter drops ~40%, rotation slows down
        const t = (p - 0.20) / 0.25
        activeColor.copy(colorRed).lerp(colorAmber, t)
        jitterAmp = THREE.MathUtils.lerp(0.20, 0.11, t)
        rotBaseSpeed = THREE.MathUtils.lerp(0.016, 0.011, t)

        wireMesh.visible = true
        wireMaterial.opacity = 0.95
        solidMesh.visible = false
        glowMesh.visible = false
        scanRing.visible = false
        stage = 1
      } else if (p < 0.75) {
        // [0.45 - 0.75]: EXECUTING
        // Amber color, scan ring sweeps across surface, jitter stabilizes further
        const t = (p - 0.45) / 0.30
        activeColor.copy(colorAmber)
        jitterAmp = THREE.MathUtils.lerp(0.11, 0.04, t)
        rotBaseSpeed = THREE.MathUtils.lerp(0.011, 0.007, t)

        wireMesh.visible = true
        wireMaterial.opacity = 0.90
        solidMesh.visible = t > 0.5
        solidMaterial.opacity = THREE.MathUtils.lerp(0.0, 0.4, t)

        scanRing.visible = true
        ringMaterial.color.copy(colorAmber)
        ringMaterial.opacity = 0.85
        // Scan ring sweeps up and down along Y axis
        scanRing.position.y = Math.sin(time * 3.5) * (radius * 0.75)
        scanRing.rotation.z += 0.04
        glowMesh.visible = false
        stage = 2
      } else {
        // [0.75 - 1.00]: VERIFIED
        // Amber -> Green lerp, jitter reaches 0 (perfect crystal), solid faceted mesh emerges,
        // rotation settles into calm state, breathing outer glow ramps in
        const t = (p - 0.75) / 0.25
        activeColor.copy(colorAmber).lerp(colorGreen, t)
        jitterAmp = THREE.MathUtils.lerp(0.04, 0.00, t)
        rotBaseSpeed = THREE.MathUtils.lerp(0.007, 0.004, t)

        wireMesh.visible = t < 0.9
        wireMaterial.opacity = THREE.MathUtils.lerp(0.9, 0.0, t)

        solidMesh.visible = true
        solidMaterial.opacity = THREE.MathUtils.lerp(0.4, 0.95, t)
        solidMaterial.color.copy(activeColor)

        // Outer glow breathing
        glowMesh.visible = true
        const breathe = 1.0 + Math.sin(time * 2.0) * 0.03
        glowMesh.scale.set(breathe, breathe, breathe)
        glowMaterial.color.copy(activeColor)
        glowMaterial.opacity = THREE.MathUtils.lerp(0.1, 0.5, t)

        scanRing.visible = t < 0.3
        ringMaterial.opacity = THREE.MathUtils.lerp(0.85, 0.0, t / 0.3)
        stage = 3
      }

      // Material color sync
      wireMaterial.color.copy(activeColor)
      particleMaterial.color.copy(activeColor)

      // Notify parent when discrete stage changes
      if (onStateChange && lastStageRef.current !== stage) {
        lastStageRef.current = stage
        onStateChange(stage, p)
      }

      // 3. Dynamic Vertex Jitter Update (applies to both wireframe & solid geometries)
      const wireArr = wireGeo.attributes.position.array
      const solidArr = solidGeo.attributes.position.array

      for (let i = 0; i < posAttr.count; i++) {
        const ox = origPositions[i * 3]
        const oy = origPositions[i * 3 + 1]
        const oz = origPositions[i * 3 + 2]

        const noiseVal = calcNoise(ox, oy, oz, time)
        const displacement = noiseVal * jitterAmp

        const dx = ox + (ox / radius) * displacement
        const dy = oy + (oy / radius) * displacement
        const dz = oz + (oz / radius) * displacement

        wireArr[i * 3] = dx
        wireArr[i * 3 + 1] = dy
        wireArr[i * 3 + 2] = dz

        solidArr[i * 3] = dx
        solidArr[i * 3 + 1] = dy
        solidArr[i * 3 + 2] = dz
      }

      wireGeo.attributes.position.needsUpdate = true
      solidGeo.attributes.position.needsUpdate = true
      solidGeo.computeVertexNormals()

      // 4. Scroll-governed Rotation & Settling Behavior
      const speed = isHoveredRef.current ? rotBaseSpeed * 0.3 : rotBaseSpeed
      wireMesh.rotation.y += speed
      wireMesh.rotation.x += speed * 0.55
      solidMesh.rotation.copy(wireMesh.rotation)
      glowMesh.rotation.copy(wireMesh.rotation)

      // Scale with entrance & hover
      const baseScale = bootScale * (isHoveredRef.current ? 1.04 : 1.0)
      wireMesh.scale.set(baseScale, baseScale, baseScale)
      solidMesh.scale.set(baseScale, baseScale, baseScale)
      glowMesh.scale.set(baseScale * 1.12, baseScale * 1.12, baseScale * 1.12)

      // 5. Camera mouse parallax
      camera.position.x += (mouseX * 0.35 - camera.position.x) * 0.05
      camera.position.y += (mouseY * 0.35 - camera.position.y) * 0.05
      camera.lookAt(0, 0, 0)

      // 6. Click pulse wave expansion
      if (pulseTriggerRef.current) {
        pulseRing.scale.multiplyScalar(1.05)
        pulseRingMat.opacity *= 0.94
        if (pulseRingMat.opacity < 0.02) {
          pulseTriggerRef.current = false
          pulseRingMat.opacity = 0.0
        }
      }

      // Ambient particle slow orbit
      particles.rotation.y += 0.001

      renderer.render(scene, camera)
    }

    animate()

    return () => {
      cancelAnimationFrame(animId)
      window.removeEventListener('scroll', updateScroll)
      window.removeEventListener('resize', handleResize)
      container.removeEventListener('mousemove', handleMouseMove)
      container.removeEventListener('mouseenter', handleMouseEnter)
      container.removeEventListener('mouseleave', handleMouseLeave)
      container.removeEventListener('click', handleClick)
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
      baseGeo.dispose()
      wireGeo.dispose()
      solidGeo.dispose()
      wireMaterial.dispose()
      solidMaterial.dispose()
      glowMaterial.dispose()
      ringMaterial.dispose()
      pulseRingGeo.dispose()
      pulseRingMat.dispose()
      particleGeo.dispose()
      particleMaterial.dispose()
      renderer.dispose()
    }
  }, [])

  if (!hasWebGL) {
    return (
      <div className="w-full h-full flex items-center justify-center">
        <div className="w-48 h-48 rounded-full border border-[var(--green)]/40 bg-[var(--surface-1)] flex items-center justify-center shadow-lg shadow-[var(--green)]/10">
          <span className="font-mono text-xs font-semibold text-[var(--green)] tracking-wider">
            [VERIFIED 2D CORE]
          </span>
        </div>
      </div>
    )
  }

  return (
    <div
      ref={containerRef}
      className="w-full h-full cursor-pointer relative select-none"
      title="Click to pulse verification waveform"
    />
  )
}
