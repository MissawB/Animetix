import { useState, useEffect } from 'react'
import { ClassicGame } from './components/ClassicGame'
import { EmojiGame } from './components/EmojiGame'
import { AkinetixGame } from './components/AkinetixGame'
import { ParadoxGame } from './components/ParadoxGame'
import './index.css'
import { Moon, Sun } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// ─────────────────────────────────────────────────────────────
// Theme Toggle Hook
// ─────────────────────────────────────────────────────────────
function useTheme() {
  const [theme, setTheme] = useState('dark')

  useEffect(() => {
    const savedTheme = localStorage.getItem('animetix-theme') || 'dark'
    setTheme(savedTheme)
  }, [])

  useEffect(() => {
    document.documentElement.setAttribute('data-bs-theme', theme)
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
    localStorage.setItem('animetix-theme', theme)
  }, [theme])

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light')

  return { theme, toggleTheme }
}

// ─────────────────────────────────────────────────────────────
// NavBar
// ─────────────────────────────────────────────────────────────
function NavBar({ activeTab, onTabChange, theme, toggleTheme }) {
  return (
    <div className="w-full flex items-center justify-between px-6 py-6 md:px-12 pointer-events-auto z-50">
      <div className="flex items-center gap-6">
        <button
          onClick={() => onTabChange('dashboard')}
          className="flex items-center no-underline cursor-pointer transition-transform hover:scale-105"
        >
          <img src="/img/logo/logo.png" alt="Logo" className="h-8 hidden dark:block" />
          <img src="/img/logo/white_logo.png" alt="Logo" className="h-8 dark:hidden" />
        </button>
      </div>
      
      <div className="hidden lg:flex items-center gap-8">
        <a href={`${API_BASE}/daily_challenge`} className="bg-anime-accent hover:bg-anime-accent-dark text-black font-black italic manga-font text-[10px] py-2 px-6 rounded-xl shadow-lg hover:scale-105 transition-all no-underline">
          Défi du jour
        </a>
        <a href={`${API_BASE}/leaderboard`} className="manga-font text-xs hover:text-anime-accent transition-colors no-underline text-anime-light-text dark:text-anime-dark-text uppercase font-black italic">
          Classement
        </a>
        <a href={`${API_BASE}/latent_space`} className="manga-font text-xs hover:text-anime-accent transition-colors no-underline text-anime-light-text dark:text-anime-dark-text uppercase font-black italic">
          Espace Latent
        </a>
      </div>

      <div className="flex items-center gap-4">
        <button onClick={toggleTheme} className="p-2 rounded-full hover:bg-black/10 dark:hover:bg-white/10 transition-colors text-anime-light-text dark:text-anime-dark-text">
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Dashboard (Match the old Django template)
// ─────────────────────────────────────────────────────────────
const MODES_SOLO = [
  { id: 'classic', titre_brush_1: 'CLASSIC', titre_brush_2: 'MODE', description: 'Trouvez le titre mystère grâce à la similarité sémantique.', icon_url: '/img/ui/frieren.png', gradient: 'from-blue-600 via-indigo-500 to-blue-400', tab: 'classic' },
  { id: 'emoji', titre_brush_1: 'EMOJI', titre_brush_2: 'DECODE', description: 'Déchiffrez les symboles pour identifier l\'œuvre cachée.', icon_url: '/img/ui/Shaman_king.png', gradient: 'from-orange-600 via-red-500 to-amber-400', tab: 'emoji' },
  { id: 'animinator', titre_brush_1: 'ANIMINATOR', titre_brush_2: 'ORACLE', description: 'Posez vos questions à l\'Oracle pour débusquer le secret.', icon_url: '/img/ui/Sinbad.png', gradient: 'from-purple-700 via-violet-600 to-purple-400', tab: 'rag' },
  { id: 'akinetix', titre_brush_1: 'AKINETIX', titre_brush_2: 'DEVIN', description: 'L\'IA analyse vos pensées pour deviner ce que vous cachez.', icon_url: '/img/ui/Saiki.png', gradient: 'from-pink-600 via-rose-500 to-pink-400', tab: 'akinetix' },
  { id: 'paradox', titre_brush_1: 'PARADOX', titre_brush_2: 'QUEST', description: 'Débusquez l\'intrus parmi les scénarios générés par l\'IA.', icon_url: '/img/ui/Steins_gate.png', gradient: 'from-red-700 via-rose-600 to-red-400', tab: 'paradox' },
  { id: 'vision', titre_brush_1: 'VISION', titre_brush_2: 'QUEST', description: 'Défiez la reconnaissance visuelle de l\'IA en décrivant l\'image.', icon_url: '/img/ui/SAO.png', gradient: 'from-cyan-600 via-blue-500 to-sky-400', djangoUrl: '/vision_quest' },
  { id: 'blind', titre_brush_1: 'BLIND', titre_brush_2: 'TEST', description: 'Devinez l\'animé à partir de son opening ou ending.', icon_url: '/img/ui/Kaori.png', gradient: 'from-green-600 via-teal-500 to-emerald-400', djangoUrl: '/blindtest' },
  { id: 'cover', titre_brush_1: 'COVER', titre_brush_2: 'TEST', description: 'Devinez le manga à partir de sa couverture (JA/FR).', icon_url: '/img/ui/Bakuman.png', gradient: 'from-amber-600 via-yellow-500 to-orange-400', djangoUrl: '/covertest' },
]

const MODES_MULTI = [
  { titre: 'Undercover', description: "Débusquez l'intrus.", djangoUrl: '/undercover_party_setup', icon_url: '/img/ui/Light.png' },
  { titre: 'Code Manga', description: 'Agents secrets.', djangoUrl: '/codemanga', icon_url: '/img/ui/code_manga.png' },
]

const MODES_CREATIVE = [
  { titre: "Fusion d'Univers", titre_sub: 'CRÉEZ DES MONDES UNIQUES À TOUT MOMENT', djangoUrl: '/archetypist', fusion_image: '/img/ui/Fusion.png' }
]

function Dashboard({ onNavigate }) {
  const handleClick = (mode) => {
    if (mode.tab) {
      onNavigate(mode.tab);
    } else if (mode.djangoUrl) {
      // Rediriger vers l'ancienne page Django pour les fonctionnalités non encore portées sur React
      window.location.href = `${API_BASE}${mode.djangoUrl}`;
    }
  };

  return (
    <div className="w-full animate-fade-in pb-20">
      {/* SECTION HERO CONTENT */}
      <section className="max-w-[1600px] mx-auto px-6 md:px-20 py-10 md:pb-32 min-h-[500px] flex flex-col md:flex-row items-center justify-between">
        <div className="z-10 md:w-1/2">
          <h1 className="text-5xl md:text-6xl font-black italic tracking-tighter mb-8 uppercase text-anime-light-text dark:text-anime-dark-text manga-font leading-none">
            ANIMETIX
          </h1>
          <p className="text-xl mb-10 text-black/70 dark:text-white/70 leading-relaxed max-w-lg font-medium">
            L'intelligence artificielle au service de votre passion.
          </p>
          <div className="flex flex-wrap gap-6">
            <button
              onClick={() => onNavigate('classic')}
              className="bg-anime-accent hover:bg-anime-accent-dark text-black font-black italic manga-font text-sm py-4 px-10 rounded-2xl shadow-2xl hover:scale-105 transition-all inline-block"
            >
              Mode Classic
            </button>
            <a
              href={`${API_BASE}/leaderboard`}
              className="bg-black dark:bg-[#2a2a3a] text-white font-black italic manga-font py-4 px-10 rounded-2xl text-sm tracking-wider uppercase transition-all duration-300 hover:bg-black/80 dark:hover:bg-[#3a3a4a] inline-block shadow-2xl no-underline"
            >
              Classement
            </a>
          </div>
        </div>
        <div className="md:w-1/2 relative mt-10 md:mt-0 flex justify-center">
          <img src="/img/hero.png" alt="Hero Image" className="w-[600px] z-10 relative animate-float drop-shadow-2xl" />
        </div>
      </section>

      {/* CONTENT WRAPPER */}
      <div className="max-w-[1600px] mx-auto px-6 md:px-10 pb-20 mt-12 bg-white dark:bg-[#1a1a2e] rounded-[3rem] shadow-xl transition-colors duration-500 pt-12">
        
        {/* SECTION MODES SOLO */}
        <section className="py-12">
          <h2 className="text-3xl font-black mb-8 flex items-baseline text-anime-light-text dark:text-anime-dark-text uppercase italic manga-font">
            Défis Solo<span className="text-anime-accent text-4xl leading-none ml-1">.</span>
          </h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-y-12 gap-x-12">
            {MODES_SOLO.map((mode, idx) => (
              <div
                key={mode.id}
                onClick={() => handleClick(mode)}
                className="relative w-full h-[200px] group cursor-pointer animate-float"
                style={{ animationDelay: `${idx * 0.1}s` }}
              >
                {/* 1. BACKGROUND LAYER */}
                <div className="absolute inset-0 rounded-[24px] overflow-hidden shadow-lg transition-transform duration-500 origin-bottom group-hover:scale-105">
                  <div className={`absolute inset-0 bg-gradient-to-br ${mode.gradient}`}></div>
                </div>

                {/* 2. TEXT LAYER */}
                <div className="absolute top-[5%] -left-4 z-30 transition-transform duration-500 group-hover:scale-110 pointer-events-none">
                  <h2 className="manga-font text-white text-4xl leading-[0.7] -rotate-12 tracking-tighter uppercase whitespace-nowrap drop-shadow-xl" style={{ textShadow: '-1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000, 0 4px 10px rgba(0,0,0,0.5)' }}>
                    {mode.titre_brush_1}<br/>
                    <span className="text-anime-accent text-2xl ml-6 tracking-normal">{mode.titre_brush_2}</span>
                  </h2>
                  <p className="manga-font text-white text-xs italic mt-8 ml-10 opacity-90 tracking-wider leading-relaxed max-w-[60%] drop-shadow-md" style={{ textShadow: '1px 1px 2px rgba(0,0,0,0.8)' }}>
                    {mode.description}
                  </p>
                </div>

                {/* 3. RENDER LAYER */}
                <img 
                  src={mode.icon_url} 
                  alt={mode.id} 
                  className="absolute bottom-0 -right-4 h-[105%] w-auto object-contain z-20 transition-all duration-500 origin-bottom group-hover:scale-110"
                  style={{ filter: 'drop-shadow(0 10px 10px rgba(0,0,0,0.4))' }}
                />
              </div>
            ))}
          </div>
        </section>

        {/* SECTION MODES MULTI */}
        <section className="px-10 py-12 bg-black/5 dark:bg-white/5 rounded-[3rem]">
          <h2 className="text-3xl font-black mb-10 flex items-baseline text-anime-light-text dark:text-anime-dark-text uppercase italic manga-font">
            Entre Amis<span className="text-anime-accent text-3xl leading-none ml-1">.</span>
          </h2>
          <div className="flex flex-wrap gap-12 justify-center pb-8">
            {MODES_MULTI.map((mode) => (
              <button
                key={mode.titre}
                onClick={() => handleClick(mode)}
                className="collection-card rounded-3xl p-8 relative flex items-center justify-between w-full md:w-[500px] h-[220px] shadow-2xl transition-all duration-300 hover:scale-105 group text-left overflow-hidden"
              >
                <div className="z-10">
                  <h3 className="text-black text-4xl font-black italic tracking-tighter manga-font">{mode.titre}</h3>
                  <p className="text-black/80 text-xs font-bold uppercase tracking-widest mt-2">{mode.description}</p>
                </div>
                <img src={mode.icon_url} className="absolute right-6 bottom-0 h-[240px] drop-shadow-lg transition-transform group-hover:scale-110" alt={mode.titre} />
              </button>
            ))}
          </div>
        </section>

        {/* SECTION CRÉATIVE */}
        <section className="py-16">
          <h2 className="text-3xl font-black mb-12 flex items-baseline text-anime-light-text dark:text-anime-dark-text uppercase italic manga-font">
            Créative<span className="text-anime-accent text-4xl leading-none ml-1">.</span>
          </h2>
          
          {MODES_CREATIVE.map((mode) => (
            <button
              key={mode.titre}
              onClick={() => handleClick(mode)}
              className="w-full block group text-left"
            >
              <div className="relative w-full h-[500px] bg-[#050505] rounded-[3rem] overflow-hidden shadow-2xl flex flex-col justify-between p-12 transition-transform duration-500 hover:scale-[1.01]">
                
                <div className="absolute inset-0 w-full h-full flex items-center justify-center z-10 p-4">
                  <img src={mode.fusion_image} className="max-h-full max-w-full object-contain grayscale opacity-60 group-hover:grayscale-0 group-hover:opacity-100 group-hover:scale-105 transition-all duration-700" alt="Fusion" />
                </div>

                <div className="absolute bottom-0 left-0 w-full h-[180px] bg-gradient-to-t from-black via-black/80 to-transparent z-20"></div>

                <div className="relative z-30 mt-auto">
                  <h1 className="text-white text-5xl md:text-7xl lg:text-9xl font-black uppercase tracking-tighter leading-none mb-3 manga-font italic" style={{ textShadow: '0 10px 30px rgba(0,0,0,0.5)' }}>
                    {mode.titre}
                  </h1>
                  <p className="text-anime-accent text-sm md:text-lg lg:text-xl font-black uppercase tracking-[0.2em] manga-font opacity-90">
                    {mode.titre_sub}
                  </p>
                </div>
              </div>
            </button>
          ))}
        </section>

      </div>
    </div>
  )
}


// ─────────────────────────────────────────────────────────────
// Oracle RAG Panel
// ─────────────────────────────────────────────────────────────
function OraclePanel() {
  const [query, setQuery] = useState('')
  const [mediaType, setMediaType] = useState('anime')
  const [answer, setAnswer] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [streamTokens, setStreamTokens] = useState([])

  const handleAsk = async () => {
    if (!query.trim()) return
    setIsLoading(true)
    setAnswer(null)
    setError(null)
    setStreamTokens([])

    try {
      const res = await fetch(`${API_BASE}/api/v1/search/rag/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ query, media_type: mediaType }),
      })

      if (!res.ok) throw new Error(`API Error: ${res.status}`)

      const contentType = res.headers.get('content-type') || ''
      if (contentType.includes('text/event-stream')) {
        const reader = res.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop()
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const token = line.slice(6)
              if (token !== '[DONE]') setStreamTokens(prev => [...prev, token])
            }
          }
        }
        setAnswer(streamTokens.join(''))
      } else {
        const data = await res.json()
        setAnswer(data.answer || data.text || JSON.stringify(data))
      }
    } catch (e) {
      setError(`Erreur: ${e.message}`)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pt-10 pb-20 animate-fade-in px-6">
      <h2 className="text-4xl font-black mb-8 flex items-baseline text-anime-light-text dark:text-anime-dark-text uppercase italic manga-font">
        Oracle IA<span className="text-anime-accent text-5xl leading-none ml-1">.</span>
      </h2>

      <div className="glass-card p-8">
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Posez une question sur un anime..."
          className="input-field mb-4 min-h-[100px]"
        />
        <button onClick={handleAsk} disabled={isLoading || !query.trim()} className="btn-primary">
          {isLoading ? 'Réflexion...' : 'Demander'}
        </button>
        
        {streamTokens.length > 0 && !answer && (
          <div className="mt-8 p-6 bg-black/5 dark:bg-white/5 rounded-2xl">
            <p className="text-sm font-medium animate-pulse mb-2 text-anime-accent">L'Oracle parle...</p>
            <p className="text-anime-light-text dark:text-anime-dark-text leading-relaxed">{streamTokens.join('')}</p>
          </div>
        )}
        
        {answer && (
          <div className="mt-8 p-6 bg-black/5 dark:bg-white/5 rounded-2xl border-l-4 border-anime-accent">
            <p className="text-anime-light-text dark:text-anime-dark-text leading-relaxed whitespace-pre-wrap">{answer}</p>
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────
// Root App
// ─────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard')
  const { theme, toggleTheme } = useTheme()

  return (
    <div className="min-h-screen">
      {/* Top Hero Background Section */}
      {activeTab === 'dashboard' && (
        <div className="absolute top-0 left-0 w-full hero-bg h-[600px] z-0 transition-all duration-500 shadow-sm" />
      )}
      
      <div className="relative z-10 flex flex-col min-h-screen">
        <NavBar activeTab={activeTab} onTabChange={setActiveTab} theme={theme} toggleTheme={toggleTheme} />

        <main className="flex-grow">
          {activeTab === 'dashboard' && <Dashboard onNavigate={setActiveTab} />}
          {activeTab === 'classic'   && (
            <div className="max-w-4xl mx-auto pt-10 px-6 pb-20">
              <ClassicGame />
            </div>
          )}
          {activeTab === 'emoji' && <EmojiGame />}
          {activeTab === 'akinetix' && <AkinetixGame />}
          {activeTab === 'paradox' && <ParadoxGame />}
          {activeTab === 'rag'       && <OraclePanel />}
        </main>

        <footer className="py-8 text-center bg-black/5 dark:bg-black/20">
          <p className="text-black/40 dark:text-white/40 text-xs font-semibold uppercase tracking-widest manga-font">
            Animetix SPA · Propulsé par Vite & React
          </p>
        </footer>
      </div>
    </div>
  )
}

