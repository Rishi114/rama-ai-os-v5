import { useRef, useState, useEffect, useCallback, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls } from '@react-three/drei'
import * as THREE from 'three'

// ── Types ─────────────────────────────────────────────────────────────────
type Mode = 'idle' | 'listening' | 'processing' | 'responding' | 'security'
type Intent = 'ORCHESTRATOR' | 'CODER' | 'ANALYST' | 'SECURITY' | 'CREATIVE' | 'VISION' | 'CEO_MODE'
interface Message { role: 'user' | 'rama'; text: string; intent?: Intent; ts: string }

const ORCHESTRATOR_URL = import.meta.env.VITE_ORCHESTRATOR_URL || 'http://localhost:3500'

// ── Colour map per intent ──────────────────────────────────────────────────
const INTENT_COLOR: Record<string, string> = {
  ORCHESTRATOR: '#00e5ff',
  CODER: '#b388ff',
  ANALYST: '#69f0ae',
  SECURITY: '#ff5252',
  CREATIVE: '#ffab40',
  VISION: '#40c4ff',
  CEO_MODE: '#ffd740',
}

// ── 3D RAMA Core ──────────────────────────────────────────────────────────
function RamaCore({ mode, intent }: { mode: Mode; intent: Intent }) {
  const sphereRef = useRef<THREE.Mesh>(null)
  const ring1Ref  = useRef<THREE.Mesh>(null)
  const ring2Ref  = useRef<THREE.Mesh>(null)
  const ring3Ref  = useRef<THREE.Mesh>(null)
  const timeRef   = useRef(0)

  const color = INTENT_COLOR[intent] || '#00e5ff'
  const isActive = mode !== 'idle'

  useFrame((_, delta) => {
    timeRef.current += delta
    const t = timeRef.current
    const speed = isActive ? 2.5 : 0.4

    if (sphereRef.current) {
      const scale = 1 + Math.sin(t * (isActive ? 3 : 1)) * (isActive ? 0.08 : 0.02)
      sphereRef.current.scale.setScalar(scale)
      sphereRef.current.rotation.y += delta * speed * 0.3
    }
    if (ring1Ref.current) {
      ring1Ref.current.rotation.x += delta * speed * 0.7
      ring1Ref.current.rotation.z += delta * speed * 0.3
    }
    if (ring2Ref.current) {
      ring2Ref.current.rotation.y += delta * speed * 0.5
      ring2Ref.current.rotation.x += delta * speed * 0.2
    }
    if (ring3Ref.current) {
      ring3Ref.current.rotation.z += delta * speed * 0.9
      ring3Ref.current.rotation.y -= delta * speed * 0.4
    }
  })

  return (
    <group>
      {/* Central sphere */}
      <mesh ref={sphereRef}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isActive ? 0.8 : 0.3}
          wireframe
          transparent
          opacity={0.7}
        />
      </mesh>

      {/* Inner glow sphere */}
      <mesh>
        <sphereGeometry args={[0.6, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isActive ? 1.5 : 0.5}
          transparent
          opacity={0.15}
        />
      </mesh>

      {/* Orbital rings */}
      {[ring1Ref, ring2Ref, ring3Ref].map((ref, i) => (
        <mesh key={i} ref={ref} rotation={[Math.PI / (2 + i), i * 0.8, 0]}>
          <torusGeometry args={[1.4 + i * 0.25, 0.012, 8, 64]} />
          <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.6} />
        </mesh>
      ))}

      {/* Point light at centre */}
      <pointLight color={color} intensity={isActive ? 3 : 1} distance={6} />
    </group>
  )
}

// ── HUD overlay numbers ───────────────────────────────────────────────────
function HUDMetric({ label, value, color = '#00e5ff' }: { label: string; value: string; color?: string }) {
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{ fontSize: 11, color: '#4fc3f7', letterSpacing: 2, marginBottom: 2 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 700, color, fontFamily: 'monospace' }}>{value}</div>
    </div>
  )
}

// ── Main App ──────────────────────────────────────────────────────────────
export default function App() {
  const [mode, setMode]       = useState<Mode>('idle')
  const [intent, setIntent]   = useState<Intent>('ORCHESTRATOR')
  const [messages, setMessages] = useState<Message[]>([
    { role: 'rama', text: 'RAMA OS v5.0 online. Awaiting directives, Boss.', intent: 'ORCHESTRATOR', ts: new Date().toISOString() }
  ])
  const [input, setInput]     = useState('')
  const [ceoMode, setCeoMode] = useState(false)
  const [listening, setListening] = useState(false)
  const [security, setSecurity] = useState({ status: 'SCANNING', alerts: 0 })
  const [metrics, setMetrics]  = useState({ cpu: '--', ram: '--', neural: '--' })
  const [tab, setTab]          = useState<'chat' | 'agents' | 'system'>('chat')
  const [skills, setSkills]    = useState<string[]>([])
  const chatEndRef = useRef<HTMLDivElement>(null)
  const recognitionRef = useRef<SpeechRecognition | null>(null)

  // ── Auto-scroll ──────────────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // ── Poll security + metrics ──────────────────────────────────────────
  useEffect(() => {
    const poll = async () => {
      try {
        const [secR, memR] = await Promise.allSettled([
          fetch(`${ORCHESTRATOR_URL}/api/security/status`),
          fetch(`${ORCHESTRATOR_URL}/health`),
        ])
        if (secR.status === 'fulfilled' && secR.value.ok) {
          const d = await secR.value.json()
          setSecurity({ status: d.status || 'NOMINAL', alerts: d.alert_count || 0 })
        }
        if (memR.status === 'fulfilled' && memR.value.ok) {
          const d = await memR.value.json()
          setMetrics({
            cpu: `${Math.floor(Math.random() * 30 + 10)}%`,
            ram: `${Math.floor(Math.random() * 40 + 20)}%`,
            neural: d.models?.length ? `${d.models.length} models` : 'cloud',
          })
        }
      } catch { /* offline */ }
    }
    poll()
    const id = setInterval(poll, 8000)
    return () => clearInterval(id)
  }, [])

  // ── Send message ─────────────────────────────────────────────────────
  const send = useCallback(async (text: string) => {
    if (!text.trim()) return
    const userMsg: Message = { role: 'user', text, ts: new Date().toISOString() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setMode('processing')

    try {
      const res = await fetch(`${ORCHESTRATOR_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: messages.slice(-6).map(m => ({ role: m.role === 'user' ? 'user' : 'assistant', content: m.text })),
          ceo_mode: ceoMode,
        }),
      })
      if (res.ok) {
        const data = await res.json()
        const ramaIntent = (data.intent as Intent) || 'ORCHESTRATOR'
        setIntent(ramaIntent)
        setMode('responding')
        setMessages(prev => [...prev, {
          role: 'rama',
          text: data.response || 'No response.',
          intent: ramaIntent,
          ts: new Date().toISOString(),
        }])

        // TTS
        if ('speechSynthesis' in window && data.response) {
          const utt = new SpeechSynthesisUtterance(data.response.slice(0, 200))
          utt.rate = 1.1; utt.pitch = 0.85
          speechSynthesis.speak(utt)
        }
      } else {
        throw new Error(`HTTP ${res.status}`)
      }
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'rama',
        text: `Orchestrator offline, Boss. Start the backend: cd backend && uvicorn orchestrator.main:app --reload --port 3500\n\nError: ${e}`,
        intent: 'SECURITY',
        ts: new Date().toISOString(),
      }])
    }
    setTimeout(() => setMode('idle'), 2000)
  }, [messages, ceoMode])

  // ── Voice input ───────────────────────────────────────────────────────
  const toggleVoice = useCallback(() => {
    if (!('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
      alert('Speech recognition not supported in this browser')
      return
    }
    if (listening) {
      recognitionRef.current?.stop()
      setListening(false)
      return
    }
    const SRClass = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition
    const rec: SpeechRecognition = new SRClass()
    rec.continuous = true
    rec.interimResults = false
    rec.lang = 'en-IN'
    rec.onresult = (e: SpeechRecognitionEvent) => {
      const transcript = e.results[e.results.length - 1][0].transcript
      send(transcript)
    }
    rec.onend = () => setListening(false)
    rec.start()
    recognitionRef.current = rec
    setListening(true)
    setMode('listening')
  }, [listening, send])

  // ── Intent colour ─────────────────────────────────────────────────────
  const ic = INTENT_COLOR[intent] || '#00e5ff'
  const secColor = security.status === 'NOMINAL' ? '#69f0ae' : '#ff5252'

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#000', display: 'flex', flexDirection: 'column', color: '#e0e0e0', fontFamily: 'monospace' }}>

      {/* ── Top HUD bar ─────────────────────────────────────────────── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 20px', borderBottom: `1px solid ${ic}22`, background: '#050505' }}>
        <div style={{ fontSize: 13, color: ic, letterSpacing: 3, fontWeight: 700 }}>RAMA OS v5.0</div>
        <div style={{ display: 'flex', gap: 32 }}>
          <HUDMetric label="CPU" value={metrics.cpu} />
          <HUDMetric label="RAM" value={metrics.ram} />
          <HUDMetric label="NEURAL" value={metrics.neural} color={ic} />
          <HUDMetric label="SENTINEL" value={security.status} color={secColor} />
        </div>
        <div style={{ fontSize: 11, color: '#4fc3f7' }}>
          {new Date().toLocaleTimeString()} | MODE: {mode.toUpperCase()}
        </div>
      </div>

      {/* ── Main layout ─────────────────────────────────────────────── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>

        {/* ── 3D Core (left) ───────────────────────────────────────── */}
        <div style={{ width: 340, flexShrink: 0, position: 'relative' }}>
          <Canvas camera={{ position: [0, 0, 4], fov: 50 }}>
            <ambientLight intensity={0.1} />
            <Suspense fallback={null}>
              <RamaCore mode={mode} intent={intent} />
            </Suspense>
            <OrbitControls enableZoom={false} enablePan={false} autoRotate={false} />
          </Canvas>

          {/* Corner brackets */}
          {[
            { top: 8, left: 8, borderTop: `1px solid ${ic}`, borderLeft: `1px solid ${ic}` },
            { top: 8, right: 8, borderTop: `1px solid ${ic}`, borderRight: `1px solid ${ic}` },
            { bottom: 8, left: 8, borderBottom: `1px solid ${ic}`, borderLeft: `1px solid ${ic}` },
            { bottom: 8, right: 8, borderBottom: `1px solid ${ic}`, borderRight: `1px solid ${ic}` },
          ].map((style, i) => (
            <div key={i} style={{ position: 'absolute', width: 20, height: 20, ...style }} />
          ))}

          {/* Status label */}
          <div style={{ position: 'absolute', bottom: 20, left: 0, right: 0, textAlign: 'center', fontSize: 10, color: ic, letterSpacing: 2 }}>
            {mode === 'listening' ? '● LISTENING' : mode === 'processing' ? '◆ PROCESSING' : '○ STANDBY'} | {intent}
          </div>
        </div>

        {/* ── Right panel ──────────────────────────────────────────── */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', borderLeft: `1px solid ${ic}22` }}>

          {/* Tab bar */}
          <div style={{ display: 'flex', gap: 0, borderBottom: `1px solid ${ic}22` }}>
            {(['chat', 'agents', 'system'] as const).map(t => (
              <button key={t} onClick={() => setTab(t)} style={{
                flex: 1, padding: '10px 0', background: tab === t ? `${ic}11` : 'transparent',
                border: 'none', borderBottom: tab === t ? `2px solid ${ic}` : '2px solid transparent',
                color: tab === t ? ic : '#555', cursor: 'pointer', fontSize: 11, letterSpacing: 2,
              }}>
                {t.toUpperCase()}
              </button>
            ))}
          </div>

          {/* ── Chat tab ──────────────────────────────────────────── */}
          {tab === 'chat' && (
            <>
              <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
                {messages.map((m, i) => (
                  <div key={i} style={{ display: 'flex', flexDirection: m.role === 'user' ? 'row-reverse' : 'row', gap: 8 }}>
                    <div style={{
                      maxWidth: '80%', padding: '8px 12px', borderRadius: 4, fontSize: 13, lineHeight: 1.6,
                      background: m.role === 'user' ? `${ic}15` : '#0a0a0a',
                      border: `1px solid ${m.role === 'rama' ? (INTENT_COLOR[m.intent || ''] || ic) + '44' : ic + '33'}`,
                      color: '#d0d0d0',
                    }}>
                      {m.role === 'rama' && m.intent && (
                        <div style={{ fontSize: 9, color: INTENT_COLOR[m.intent] || ic, marginBottom: 4, letterSpacing: 2 }}>
                          [{m.intent}]
                        </div>
                      )}
                      <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', margin: 0 }}>{m.text}</pre>
                      <div style={{ fontSize: 9, color: '#333', marginTop: 4, textAlign: 'right' }}>
                        {new Date(m.ts).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Input bar */}
              <div style={{ padding: '10px 16px', borderTop: `1px solid ${ic}22`, display: 'flex', gap: 8 }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#555', cursor: 'pointer' }}>
                  <input type="checkbox" checked={ceoMode} onChange={e => setCeoMode(e.target.checked)} />
                  CEO MODE
                </label>
                <input
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && send(input)}
                  placeholder="Give RAMA a directive..."
                  style={{
                    flex: 1, background: '#0a0a0a', border: `1px solid ${ic}44`, borderRadius: 4,
                    color: '#d0d0d0', padding: '8px 12px', fontSize: 13, fontFamily: 'monospace',
                    outline: 'none',
                  }}
                />
                <button onClick={toggleVoice} style={{
                  padding: '8px 14px', background: listening ? '#ff525233' : `${ic}22`,
                  border: `1px solid ${listening ? '#ff5252' : ic}`, borderRadius: 4,
                  color: listening ? '#ff5252' : ic, cursor: 'pointer', fontSize: 14,
                }}>
                  {listening ? '■' : '●'}
                </button>
                <button onClick={() => send(input)} disabled={!input.trim() || mode === 'processing'} style={{
                  padding: '8px 16px', background: `${ic}22`, border: `1px solid ${ic}`,
                  borderRadius: 4, color: ic, cursor: 'pointer', fontSize: 12, letterSpacing: 1,
                }}>
                  SEND
                </button>
              </div>
            </>
          )}

          {/* ── Agents tab ──────────────────────────────────────────── */}
          {tab === 'agents' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
              {[
                { tier: 'CEO', name: 'RAMA PRIME', role: 'Orchestrator & Strategist', status: 'ACTIVE', color: '#ffd740' },
                { tier: 'Manager', name: 'SwarmRouter', role: 'Multi-LLM routing (phi3→qwen→llava→llama3)', status: 'ACTIVE', color: ic },
                { tier: 'Manager', name: 'Ghost Coder', role: 'Autonomous GitHub PR bot', status: 'STANDBY', color: '#b388ff' },
                { tier: 'Manager', name: 'Viral Empire', role: 'Content creation & upload', status: 'STANDBY', color: '#ffab40' },
                { tier: 'Employee', name: 'NetworkSentinel', role: 'Port monitoring & threat detection', status: 'ACTIVE', color: '#ff5252' },
                { tier: 'Employee', name: 'EmotionEngine', role: 'User mood detection & tone adjustment', status: 'ACTIVE', color: '#69f0ae' },
                { tier: 'Employee', name: 'LearningEngine', role: 'FAISS vector memory', status: 'ACTIVE', color: ic },
                { tier: 'Employee', name: 'ChronosDebugger', role: 'Time-travel crash analysis', status: 'READY', color: '#40c4ff' },
                { tier: 'Employee', name: 'GenesisProtocol', role: 'Self-evolving code optimiser', status: 'READY', color: '#69f0ae' },
                { tier: 'Employee', name: 'OSINT Vision', role: 'Reddit/GitHub/HN scraper', status: 'READY', color: '#b388ff' },
                { tier: 'Employee', name: 'ADB Bridge', role: 'Android device control', status: 'OFFLINE', color: '#555' },
              ].map((a, i) => (
                <div key={i} style={{ marginBottom: 8, padding: '10px 14px', background: '#0a0a0a', border: `1px solid ${a.color}33`, borderRadius: 4 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 2 }}>
                    <span style={{ fontSize: 12, color: a.color, fontWeight: 700 }}>{a.name}</span>
                    <span style={{ fontSize: 10, color: a.status === 'ACTIVE' ? '#69f0ae' : a.status === 'OFFLINE' ? '#555' : '#ffab40', letterSpacing: 1 }}>
                      {a.status}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, color: '#555' }}>[{a.tier}] {a.role}</div>
                </div>
              ))}
            </div>
          )}

          {/* ── System tab ──────────────────────────────────────────── */}
          {tab === 'system' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>
              <div style={{ marginBottom: 16, fontSize: 11, color: '#555', letterSpacing: 2 }}>SYSTEM PROTOCOLS</div>
              {[
                { name: 'Chronos Debugger', desc: 'Rewinds to pre-crash state, synthesises patch', color: '#40c4ff',
                  action: async () => { const r = await fetch(`${ORCHESTRATOR_URL}/api/reflect`, { method: 'POST' }); const d = await r.json(); send('RAMA, run chronos analysis: ' + JSON.stringify(d).slice(0, 100)) } },
                { name: 'Genesis Evolution', desc: 'Profile + rewrite slow modules', color: '#69f0ae',
                  action: () => send('RAMA, run genesis self-evolution protocol - analyse slow components') },
                { name: 'Phantom Infra', desc: 'Generate missing API endpoints on-the-fly', color: ic,
                  action: () => send('RAMA, explain phantom infrastructure and how you generate 404 backends') },
                { name: 'OSINT Scan', desc: 'Scrape GitHub trending + HN top stories', color: '#b388ff',
                  action: () => send('RAMA, scrape GitHub trending and Hacker News top stories right now') },
                { name: 'Viral Empire', desc: 'Find trends + generate content pipeline', color: '#ffab40',
                  action: () => send('RAMA, start viral empire - find trending topics and create a content plan') },
                { name: 'Security Audit', desc: 'Full network sentinel report', color: '#ff5252',
                  action: async () => { const r = await fetch(`${ORCHESTRATOR_URL}/api/security/status`); const d = await r.json(); send('RAMA, security audit result: ' + JSON.stringify(d)) } },
              ].map((p, i) => (
                <div key={i} style={{ marginBottom: 10, padding: '12px 14px', background: '#0a0a0a', border: `1px solid ${p.color}33`, borderRadius: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: 12, color: p.color, fontWeight: 700, marginBottom: 2 }}>{p.name}</div>
                    <div style={{ fontSize: 11, color: '#555' }}>{p.desc}</div>
                  </div>
                  <button onClick={p.action} style={{
                    padding: '6px 12px', background: `${p.color}15`, border: `1px solid ${p.color}55`,
                    borderRadius: 4, color: p.color, cursor: 'pointer', fontSize: 10, letterSpacing: 1,
                  }}>
                    RUN
                  </button>
                </div>
              ))}

              <div style={{ marginTop: 20, marginBottom: 8, fontSize: 11, color: '#555', letterSpacing: 2 }}>LEARN FROM GITHUB</div>
              <div style={{ display: 'flex', gap: 8 }}>
                <input id="gh-input" placeholder="https://github.com/owner/repo" style={{
                  flex: 1, background: '#0a0a0a', border: `1px solid ${ic}44`, borderRadius: 4,
                  color: '#d0d0d0', padding: '8px 12px', fontSize: 12, fontFamily: 'monospace', outline: 'none',
                }} />
                <button onClick={async () => {
                  const url = (document.getElementById('gh-input') as HTMLInputElement).value
                  if (!url) return
                  const r = await fetch(`${ORCHESTRATOR_URL}/api/skills/learn`, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ github_url: url }),
                  })
                  const d = await r.json()
                  setSkills(prev => [...prev, url.split('/').slice(-1)[0]])
                  send(`RAMA, I just added ${url} to your knowledge base. Summarise what you learned.`)
                }} style={{
                  padding: '8px 14px', background: `${ic}22`, border: `1px solid ${ic}`,
                  borderRadius: 4, color: ic, cursor: 'pointer', fontSize: 11,
                }}>
                  LEARN
                </button>
              </div>
              {skills.length > 0 && (
                <div style={{ marginTop: 10 }}>
                  {skills.map((s, i) => <span key={i} style={{ display: 'inline-block', margin: '2px 4px', padding: '2px 8px', background: `${ic}11`, border: `1px solid ${ic}33`, borderRadius: 2, fontSize: 10, color: ic }}>{s}</span>)}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Security alert banner ───────────────────────────────────── */}
      {security.status !== 'NOMINAL' && (
        <div style={{ padding: '6px 20px', background: '#ff525211', borderTop: '1px solid #ff5252', fontSize: 11, color: '#ff5252', letterSpacing: 2 }}>
          ⚠ SENTINEL ALERT — {security.alerts} threat(s) detected — STATUS: {security.status}
        </div>
      )}
    </div>
  )
}
