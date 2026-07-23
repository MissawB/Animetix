import React, { useState } from 'react';
import { Search, Wand2, Loader2 } from 'lucide-react';
import { Timeline } from '../../components/video/Timeline';
import { Inspector } from '../../components/video/Inspector';
import { useVideoRagStore } from '../../features/labs/stores/videoRagStore';
import { labService } from '../../features/labs/services/labService';
import { useAuthStore } from '../../store/authStore';
import { VideoIndexing } from '../../components/video/VideoIndexing';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_CTA,
} from './components/shared/LabKit';

const SUGGESTIONS = [
  { label: '⚔️ Combat Épique', query: 'combat épique' },
  { label: '💬 Dialogue Clé', query: 'discussion de personnages' },
  { label: '😢 Scène Émouvante', query: 'personnage triste qui pleure' },
  { label: '🔥 Action & Mouvement', query: 'mouvement rapide action' },
];

const determineSegmentType = (summary: string): 'emotion' | 'action' | 'dialogue' => {
  const text = (summary || '').toLowerCase();
  if (
    text.includes('triste') ||
    text.includes('sad') ||
    text.includes('pleure') ||
    text.includes('cry') ||
    text.includes('peur') ||
    text.includes('scared') ||
    text.includes('fear') ||
    text.includes('émotion') ||
    text.includes('emotion') ||
    text.includes('colère') ||
    text.includes('angry') ||
    text.includes('joie') ||
    text.includes('happy') ||
    text.includes('amour') ||
    text.includes('love')
  ) {
    return 'emotion';
  }
  if (
    text.includes('parle') ||
    text.includes('speak') ||
    text.includes('dit') ||
    text.includes('say') ||
    text.includes('raconte') ||
    text.includes('tell') ||
    text.includes('dialogue') ||
    text.includes('discute') ||
    text.includes('chat') ||
    text.includes('voix') ||
    text.includes('voice') ||
    text.includes('explique') ||
    text.includes('explain')
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
      const response = await labService.searchVideoSegments(searchQuery);
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
    <LabPage>
      <LabHeader
        code="Protocole · Video-RAG"
        title="Explorateur"
        accent="temporel"
        lede="Décris un moment avec tes mots et le laboratoire retrouve l'instant exact dans les vidéos indexées, par similarité vectorielle."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Sidebar / Controls */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title="Recherche sémantique">
            <div className="space-y-4">
              <div className="relative">
                <input
                  type="text"
                  aria-label="Recherche sémantique d'un moment"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearch(query)}
                  placeholder="Chercher un moment…"
                  className={`${LAB_INPUT} pl-11`}
                />
                <Search
                  className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8F94A5]"
                  aria-hidden="true"
                />
              </div>

              <button
                type="button"
                onClick={() => handleSearch(query)}
                disabled={isLoading || !query.trim()}
                className={LAB_CTA}
              >
                {isLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <>
                    <Wand2 className="h-5 w-5" aria-hidden="true" /> Explorer
                  </>
                )}
              </button>
            </div>

            {/* Suggestions */}
            <div className="mt-8 space-y-3">
              <span className={`${LAB_LABEL} block`}>Suggestions de test</span>
              <div className="flex flex-col gap-2">
                {SUGGESTIONS.map((s, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setQuery(s.query);
                      handleSearch(s.query);
                    }}
                    className="cursor-pointer rounded-xl border border-[#F4F1E8]/10 bg-transparent px-3 py-2 text-left text-xs font-medium text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          </LabPanel>

          {isAdmin && <VideoIndexing />}
        </div>

        {/* Main Content (Timeline + Inspector) */}
        <div className="lg:col-span-8">
          <LabPanel
            title="Timeline interactive"
            className="flex min-h-[400px] flex-col justify-between"
          >
            <div>
              {error && (
                <div className="mb-6 rounded-xl border border-[#E8442B]/25 bg-[#E8442B]/[0.05] p-4 text-sm font-semibold text-[#E8442B]">
                  {error}
                </div>
              )}

              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                  <Loader2
                    className="mb-4 h-12 w-12 animate-spin text-[#E8442B]"
                    aria-hidden="true"
                  />
                  <p className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
                    Recherche des vecteurs temporels…
                  </p>
                </div>
              ) : (
                <Timeline />
              )}
            </div>

            <div className="mt-6 border-t border-[#F4F1E8]/10 pt-6">
              <Inspector />
            </div>
          </LabPanel>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Décris le moment',
            body: "Formule la scène recherchée en français courant (« combat épique », « personnage triste ») ou pars d'une suggestion de test.",
          },
          {
            title: "Lance l'exploration",
            body: 'Ta requête est vectorisée puis comparée aux segments indexés ; les correspondances apparaissent sur la timeline.',
          },
          {
            title: 'Inspecte les segments',
            body: "Chaque résultat est un segment coloré (action, dialogue ou émotion) : clique dessus pour ouvrir ses détails dans l'inspecteur.",
          },
        ]}
        note="Les vidéos sont découpées en segments temporels décrits par un modèle de vision (VLM Qwen2-VL), puis ces descriptions sont projetées dans un espace vectoriel via Jina-Embeddings. Ta requête est vectorisée à son tour et comparée par similarité pour situer l'instant exact où l'événement se produit."
      />
    </LabPage>
  );
};

export default VideoRagPage;
