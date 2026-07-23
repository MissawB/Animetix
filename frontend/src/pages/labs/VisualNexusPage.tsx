import React, { useState } from 'react';
import { Video, Zap, Film, Clock, ChevronRight, Play, Lock } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { useAuthStore } from '../../store/authStore';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_CTA,
  LAB_BTN_GHOST,
} from './components/shared/LabKit';

interface VideoSegment {
  video_id: string;
  start_time: number;
  end_time: number;
  description: string;
  score: number;
  thumbnail_url?: string;
  media_title?: string;
}

const SUGGESTIONS = [
  'Explosion nucléaire stylisée',
  'Transformation magique rose',
  'Repas de groupe chaleureux',
  'Duel au sabre au clair de lune',
];

const VisualNexusPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<VideoSegment[]>([]);
  const [authError, setAuthError] = useState(false);

  const searchMutation = useMutation({
    mutationFn: (q: string) => apiClient(`/api/v1/labs/video/search/?q=${encodeURIComponent(q)}`),
    onSuccess: (data) => {
      setSearchResults(data.results || []);
    },
  });

  // Video-RAG est un mode IA (GPU) qui coûte des Berrix et requiert une session :
  // on gate avant l'appel plutôt que de laisser l'API renvoyer un 401/402 brut.
  const runSearch = (q: string) => {
    if (!useAuthStore.getState().isAuthenticated) {
      setAuthError(true);
      return;
    }
    setAuthError(false);
    searchMutation.mutate(q);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      runSearch(query);
    }
  };

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Nexus visuel"
        title="Visual"
        accent="Nexus"
        lede="Décris une scène avec tes mots et le moteur retrouve le moment exact dans des milliers d'heures d'anime, grâce à l'indexation sémantique temporelle Video-LLaVA."
      />

      {/* Recherche */}
      <LabPanel title="Recherche de scène" corner="Video-RAG">
        <form onSubmit={handleSearch} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="nexus-query" className={LAB_LABEL}>
              Description de la scène
            </label>
            <input
              id="nexus-query"
              type="text"
              aria-label="Décrire une scène à rechercher"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ex. : un combat sous la pluie avec des éclairs bleus, un sourire triste au coucher du soleil…"
              className={LAB_INPUT}
            />
          </div>

          <button
            type="submit"
            disabled={searchMutation.isPending || !query.trim()}
            className={LAB_CTA}
          >
            {searchMutation.isPending ? (
              <Zap className="h-6 w-6 animate-spin" />
            ) : (
              'Scanner le multivers'
            )}
          </button>

          <div className="flex flex-wrap items-center gap-3">
            <span className={LAB_LABEL}>Suggestions</span>
            {SUGGESTIONS.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => {
                  setQuery(suggestion);
                  runSearch(suggestion);
                }}
                className={LAB_BTN_GHOST}
              >
                {suggestion}
              </button>
            ))}
          </div>

          {authError && (
            <div className="rounded-2xl border border-[#E8442B]/30 bg-[#E8442B]/5 p-8 text-center">
              <Lock className="mx-auto mb-4 h-8 w-8 text-[#E8442B]" aria-hidden="true" />
              <h4 className="font-manga text-sm font-black uppercase italic text-[#F4F1E8]">
                Connexion requise
              </h4>
              <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-[#8F94A5]">
                Ce mode utilise l'IA (GPU) et coûte des Berrix. Connecte-toi pour scanner le
                multivers.
              </p>
              <Link to="/auth/login/" className={`${LAB_BTN_GHOST} mt-4 no-underline`}>
                Se connecter
              </Link>
            </div>
          )}
        </form>
      </LabPanel>

      {/* Résultats */}
      <div className="mt-10">
        <AnimatePresence mode="wait">
          {searchMutation.isPending ? (
            <motion.div
              key="pending"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3"
            >
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="aspect-video animate-pulse rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]"
                />
              ))}
            </motion.div>
          ) : searchResults.length > 0 ? (
            <motion.div
              key="results"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <LabPanel title="Segments identifiés" corner={`${searchResults.length} moments`}>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {searchResults.map((segment, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: idx * 0.1 }}
                    >
                      <article className="group overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] transition-colors hover:border-[#FDB913]/40">
                        <div className="relative aspect-video border-b border-[#F4F1E8]/10 bg-[#0B0C10]">
                          <div className="absolute inset-0 flex items-center justify-center">
                            <Film className="h-12 w-12 text-[#8F94A5]/50" aria-hidden="true" />
                          </div>

                          <div className="absolute inset-0 flex items-center justify-center bg-[#0B0C10]/60 opacity-0 transition-opacity group-hover:opacity-100">
                            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-[#E8442B]">
                              <Play
                                className="h-7 w-7 fill-current text-[#F4F1E8]"
                                aria-hidden="true"
                              />
                            </div>
                          </div>

                          <div className="absolute bottom-3 right-3 flex items-center gap-2 rounded-lg border border-[#F4F1E8]/10 bg-[#0B0C10]/80 px-3 py-1 font-mono text-[10px] font-bold text-[#F4F1E8]">
                            <Clock className="h-3 w-3 text-[#FDB913]" aria-hidden="true" />
                            {Math.floor(segment.start_time / 60)}:
                            {(segment.start_time % 60).toString().padStart(2, '0')} -{' '}
                            {Math.floor(segment.end_time / 60)}:
                            {(segment.end_time % 60).toString().padStart(2, '0')}
                          </div>

                          <span className="absolute left-3 top-3 rounded-full border border-[#FDB913]/40 bg-[#0B0C10]/80 px-3 py-1 text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                            Match {Math.round(segment.score * 100)} %
                          </span>
                        </div>

                        <div className="p-6">
                          <h4 className="font-manga truncate text-lg font-black uppercase italic text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
                            {segment.media_title || `Vidéo #${segment.video_id}`}
                          </h4>
                          <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-[#8F94A5]">
                            «&nbsp;{segment.description}&nbsp;»
                          </p>
                          <div className="mt-4 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#FDB913] opacity-0 transition-opacity group-hover:opacity-100">
                            Extraire ce segment{' '}
                            <ChevronRight className="h-3 w-3" aria-hidden="true" />
                          </div>
                        </div>
                      </article>
                    </motion.div>
                  ))}
                </div>
              </LabPanel>
            </motion.div>
          ) : (
            <LabEmpty
              icon={<Video className="h-20 w-20" aria-hidden="true" />}
              title="Moteur optique prêt"
              hint="Décris une scène dans le champ ci-dessus, ou pars d'une suggestion : les segments correspondants s'afficheront ici avec leur minutage."
            />
          )}
        </AnimatePresence>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Décris la scène',
            body: 'Formule le moment recherché avec tes mots — ambiance, action, couleurs : « un combat sous la pluie », « un sourire triste au coucher du soleil ».',
          },
          {
            title: 'Lance le scan',
            body: "Le moteur interroge l'index sémantique de la base de clips. Sans inspiration, clique sur une suggestion pour un scan immédiat.",
          },
          {
            title: 'Lis les segments',
            body: 'Chaque carte affiche le titre de la vidéo, le passage exact (minutage de début et de fin) et un score de correspondance avec ta description.',
          },
        ]}
        note="Les clips sont préalablement décrits par un modèle multimodal vidéo (Video-LLaVA) puis indexés sous forme de vecteurs sémantiques avec leurs bornes temporelles. Ta requête interroge cet index par similarité vectorielle et renvoie les segments les mieux notés, timecodes compris."
      />
    </LabPage>
  );
};

export default VisualNexusPage;
