import React, { useState } from 'react';
import { Search, Wand2, Sparkles, Film, HelpCircle } from 'lucide-react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Timeline } from "../../components/video/Timeline";
import { Inspector } from "../../components/video/Inspector";
import { useVideoRagStore } from '../../features/labs/stores/videoRagStore';
import { searchVideoSegments } from '../../api';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { useAuthStore } from "../../store/authStore";
import { VideoIndexing } from "../../components/video/VideoIndexing";

const SUGGESTIONS = [
  { label: '⚔️ Combat Épique', query: 'combat épique' },
  { label: '💬 Dialogue Clé', query: 'discussion de personnages' },
  { label: '😢 Scène Émouvante', query: 'personnage triste qui pleure' },
  { label: '🔥 Action & Mouvement', query: 'mouvement rapide action' },
];

const determineSegmentType = (summary: string): 'emotion' | 'action' | 'dialogue' => {
  const text = (summary || '').toLowerCase();
  if (
    text.includes('triste') || text.includes('sad') ||
    text.includes('pleure') || text.includes('cry') ||
    text.includes('peur') || text.includes('scared') || text.includes('fear') ||
    text.includes('émotion') || text.includes('emotion') ||
    text.includes('colère') || text.includes('angry') ||
    text.includes('joie') || text.includes('happy') ||
    text.includes('amour') || text.includes('love')
  ) {
    return 'emotion';
  }
  if (
    text.includes('parle') || text.includes('speak') ||
    text.includes('dit') || text.includes('say') ||
    text.includes('raconte') || text.includes('tell') ||
    text.includes('dialogue') || text.includes('discute') || text.includes('chat') ||
    text.includes('voix') || text.includes('voice') ||
    text.includes('explique') || text.includes('explain')
  ) {
    return 'dialogue';
  }
  return 'action';
};

const VideoRagPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { setSegments, selectSegment } = useVideoRagStore();
  const { user } = useAuthStore();
  const isAdmin = user?.is_staff || false;

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const response = await searchVideoSegments(searchQuery);
      if (response && response.status === 'success' && Array.isArray(response.results)) {
        const mapped = response.results.map((res) => ({
          id: res.id || `${res.video_id}_${res.start}`,
          start: Number(res.start) || 0,
          end: Number(res.end) || 0,
          description: res.summary || '',
          type: determineSegmentType(res.summary || ''),
          video_id: String(res.video_id),
        }));
        setSegments(mapped);
        selectSegment(null); // Clear selected segment
      } else {
        setError('Aucun résultat valide retourné par le serveur.');
      }
    } catch (err) {
      const error = err as Error;
      console.error('Error during Video-RAG search:', error);
      setError(error.message || 'Une erreur est survenue lors de la recherche vectorielle.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0a0a12] text-white p-6 max-w-7xl mx-auto py-16 animate-fade-in">
        <header className="mb-12">
          <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase mb-4 text-center md:text-left">
            VIDEO-<span className="text-red-500">RAG</span> EXPLORER
          </h1>
          <p className="text-white/60 text-lg">
            Recherche sémantique et localisation temporelle de moments précis dans vos vidéos indexées via Similarité Vectorielle.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-10">
          {/* Sidebar / Controls */}
          <div className="lg:col-span-1 space-y-6">
            <Card padding="lg" className="bg-white/5 border border-white/10 shadow-xl backdrop-blur-md">
              <h3 className="text-xs font-black uppercase opacity-60 mb-4 tracking-widest flex items-center gap-2 text-red-500">
                <Sparkles className="w-4 h-4 animate-pulse" /> Recherche Sémantique
              </h3>
              
              <div className="space-y-4">
                <div className="relative">
                  <input
                    type="text"
                    aria-label="Recherche sémantique d'un moment"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch(query)}
                    placeholder="Chercher un moment..."
                    className="w-full bg-black/60 border border-white/10 rounded-xl px-4 py-3 pl-10 text-sm focus:border-red-500 outline-none transition-all placeholder-white/30 text-white"
                  />
                  <Search className="absolute left-3 top-3.5 w-4 h-4 text-white/30" />
                </div>

                <Button
                  onClick={() => handleSearch(query)}
                  disabled={isLoading || !query.trim()}
                  variant="primary"
                  fullWidth
                  className="bg-red-600 hover:bg-red-700 text-white font-bold tracking-wider py-4 text-sm uppercase flex items-center justify-center gap-2 border-none rounded-xl"
                >
                  {isLoading ? (
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <Wand2 className="w-4 h-4" /> Explorer
                    </>
                  )}
                </Button>
              </div>

              {/* Suggestions */}
              <div className="mt-8">
                <span className="text-[10px] font-black uppercase opacity-40 tracking-widest block mb-3">Suggestions de test</span>
                <div className="flex flex-col gap-2">
                  {SUGGESTIONS.map((s, idx) => (
                    <button
                      key={idx}
                      onClick={() => {
                        setQuery(s.query);
                        handleSearch(s.query);
                      }}
                      className="px-3 py-2 rounded-lg text-left text-xs font-medium border border-white/5 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white transition-all cursor-pointer"
                    >
                      {s.label}
                    </button>
                  ))}
                </div>
              </div>
            </Card>

            {isAdmin && <VideoIndexing />}
          </div>

          {/* Main Content (Timeline + Inspector) */}
          <div className="lg:col-span-3 space-y-6">
            <Card padding="lg" className="bg-black/40 border border-white/10 relative overflow-hidden min-h-[400px] flex flex-col justify-between">
              <div>
                <h2 className="text-lg font-black italic tracking-wide uppercase mb-6 flex items-center gap-2">
                  <Film className="w-5 h-5 text-red-500" /> Timeline Interactive
                </h2>
                
                {error && (
                  <div className="p-4 mb-6 bg-red-950/40 border border-red-500/20 text-red-400 rounded-xl text-sm font-semibold">
                    ⚠️ {error}
                  </div>
                )}

                {isLoading ? (
                  <div className="flex flex-col items-center justify-center py-20 text-center">
                    <div className="w-16 h-16 border-4 border-red-500 border-t-transparent rounded-full animate-spin mb-4 shadow-[0_0_15px_rgba(239,68,68,0.3)]" />
                    <p className="text-red-400 font-bold uppercase tracking-widest text-xs animate-pulse">
                      Recherche des vecteurs temporels...
                    </p>
                  </div>
                ) : (
                  <Timeline />
                )}
              </div>

              <div className="mt-6 border-t border-white/5 pt-6">
                <Inspector />
              </div>
            </Card>

            {/* Explanation card */}
            <div className="bg-white/5 border border-white/5 rounded-2xl p-6 flex gap-4 items-start">
              <HelpCircle className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-bold text-sm text-white mb-1">Comment fonctionne le Video-RAG ?</h4>
                <p className="text-xs text-white/50 leading-relaxed">
                  Le système découpe les vidéos en segments temporels, extrait leurs descriptions clés via un modèle VLM (Qwen2-VL), puis projette ces descriptions dans un espace vectoriel sémantique (via Jina-Embeddings). Votre recherche interroge directement ces vecteurs pour situer l'instant exact où l'événement recherché se produit.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default VideoRagPage;
