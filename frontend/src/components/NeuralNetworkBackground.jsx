import { useRef, useMemo, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

function NeuralNetworkParticles({ count = 2000 }) {
  const ref = useRef()
  const sphere = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    
    for (let i = 0; i < count; i++) {
      const i3 = i * 3
      const radius = 10 + Math.random() * 20
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      
      positions[i3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
      positions[i3 + 2] = radius * Math.cos(phi)
      
      // Gradient from blue to purple
      colors[i3] = 0.2 + Math.random() * 0.3 // R
      colors[i3 + 1] = 0.3 + Math.random() * 0.4 // G
      colors[i3 + 2] = 0.8 + Math.random() * 0.2 // B
    }
    
    return { positions, colors }
  }, [count])

  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.x = state.clock.elapsedTime * 0.05
      ref.current.rotation.y = state.clock.elapsedTime * 0.1
    }
  })

  return (
    <group rotation={[0, 0, Math.PI / 4]}>
      <Points ref={ref} positions={sphere.positions} colors={sphere.colors} stride={3}>
        <PointMaterial
          transparent
          vertexColors
          size={0.15}
          sizeAttenuation={true}
          depthWrite={false}
          opacity={0.6}
        />
      </Points>
    </group>
  )
}

function NeuralConnections({ count = 100 }) {
  const linesRef = useRef()
  const lines = useMemo(() => {
    const positions = []
    for (let i = 0; i < count; i++) {
      const x1 = (Math.random() - 0.5) * 30
      const y1 = (Math.random() - 0.5) * 30
      const z1 = (Math.random() - 0.5) * 30
      const x2 = x1 + (Math.random() - 0.5) * 10
      const y2 = y1 + (Math.random() - 0.5) * 10
      const z2 = z1 + (Math.random() - 0.5) * 10
      positions.push(x1, y1, z1, x2, y2, z2)
    }
    return new Float32Array(positions)
  }, [count])

  useFrame((state) => {
    if (linesRef.current) {
      linesRef.current.rotation.x = state.clock.elapsedTime * 0.03
      linesRef.current.rotation.y = state.clock.elapsedTime * 0.07
    }
  })

  return (
    <lineSegments ref={linesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={count * 2}
          array={lines}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial
        color="#6366f1"
        transparent
        opacity={0.2}
        linewidth={1}
      />
    </lineSegments>
  )
}

export default function NeuralNetworkBackground() {
  return (
    <div className="fixed inset-0 -z-10">
      <Canvas
        camera={{ position: [0, 0, 30], fov: 75 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />
        <NeuralNetworkParticles count={1500} />
        <NeuralConnections count={80} />
      </Canvas>
    </div>
  )
}
