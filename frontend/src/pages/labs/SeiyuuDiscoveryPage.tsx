import React, { useState } from 'react';
import { Mic2, Plus, Info, Music } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../utils/apiClient';
import { Button } from '../../components/ui/Button';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';
import type { IngestVoicePayload } from '../../features/labs/services/audioLabService';
import type { SeiyuuApiResponse } from '../../features/labs/types/seiyuuTypes';

import { SeiyuuIngestFormPanel } from './components/SeiyuuIngestFormPanel';
import { SeiyuuSearchFiltersPanel } from './components/SeiyuuSearchFiltersPanel';
import { SeiyuuResultCard } from './components/SeiyuuResultCard';
import { SeiyuuGuideProtocolSection } from './components/SeiyuuGuideProtocolSection';

const SeiyuuDiscoveryPage: React.FC = () => {
  const { t } = useTranslation();
  const [searchQuery, setSearchQuery] = useState('');
  const [langFilter, setLangFilter] = useState<string>('');
  const [originFilter, setOriginFilter] = useState<string>('');
  const [activeAudio, setActiveAudio] = useState<string | null>(null);
  const [audioLoading, setAudioLoading] = useState<string | null>(null);

  // Ingestion Form State
  const [showIngestForm, setShowIngestForm] = useState(false);
  const [ingestName, setIngestName] = useState('');
  const [ingestLang, setIngestLang] = useState('japanese');
  const [ingestSource, setIngestSource] = useState('');
  const [ingestDef, setIngestDef] = useState('');
  const [ingestRoles, setIngestRoles] = useState('');
  const [ingestError, setIngestError] = useState('');
  const [ingestSuccess, setIngestSuccess] = useState('');

  const { data, isLoading, refetch, isRefetching } = useQuery<SeiyuuApiResponse>({
    queryKey: ['seiyuu-discovery', searchQuery, langFilter, originFilter],
    queryFn: () => {
      let url = `/api/v1/labs/audio/seiyuu/?q=${encodeURIComponent(searchQuery)}`;
      if (langFilter) url += `&language=${langFilter}`;
      if (originFilter) url += `&origin=${originFilter}`;
      return apiClient(url);
    },
    enabled: true,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    refetch();
  };

  const playSample = (url: string) => {
    if (activeAudio === url) {
      setActiveAudio(null);
      return;
    }
    setAudioLoading(url);
    const audio = new Audio(url);
    audio
      .play()
      .then(() => {
        setAudioLoading(null);
        setActiveAudio(url);
      })
      .catch((err) => {
        console.error('Audio playback failed:', err);
        setAudioLoading(null);
        setActiveAudio(null);
      });
    audio.onended = () => setActiveAudio(null);
  };

  // Ingest Mutation
  const ingestMutation = useMutation({
    mutationFn: (payload: IngestVoicePayload) =>
      apiClient('/api/v1/labs/audio/seiyuu/ingest/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: (response) => {
      setIngestSuccess(
        t(
          'labs.seiyuu.ingest_success',
          "La voix de '{{name}}' a été ingérée et nettoyée avec succès !",
          {
            name: response.profile.name,
          },
        ),
      );
      setIngestName('');
      setIngestSource('');
      setIngestDef('');
      setIngestRoles('');
      setSearchQuery(response.profile.name);
      setTimeout(() => {
        refetch();
        setShowIngestForm(false);
        setIngestSuccess('');
      }, 3000);
    },
    onError: (err: unknown) => {
      const message = err instanceof Error ? err.message : '';
      setIngestError(
        message ||
          t(
            'labs.seiyuu.ingest_error',
            'Une erreur est survenue lors du téléchargement ou du traitement audio.',
          ),
      );
    },
  });

  const handleIngestSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIngestError('');
    setIngestSuccess('');

    if (!ingestName || !ingestSource) {
      setIngestError(
        t('labs.seiyuu.ingest_required', "Le nom et l'URL/requête YouTube sont obligatoires."),
      );
      return;
    }

    ingestMutation.mutate({
      name: ingestName,
      language: ingestLang,
      query: ingestSource,
      definition: ingestDef,
      roles: ingestRoles,
    });
  };

  return (
    <div className="min-h-screen w-full bg-[#0a0a0f] text-white pt-20 pb-32">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 relative z-10">
          {/* Header Section */}
          <header className="mb-12 relative flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/10 blur-[120px] rounded-full -z-10" />
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-6">
                <Mic2 className="w-3 h-3" /> Voice Actor Intelligent Discovery
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4 leading-none">
                SEIYUU <span className="text-emerald-500 text-glow">DISCOVERY</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                {t(
                  'labs.seiyuu.subtitle',
                  'Explorez les voix cultes (Seiyuus & Doubleurs) et ingérez de nouvelles voix à la volée.',
                )}
              </p>
            </div>
            <div>
              <Button
                onClick={() => setShowIngestForm(!showIngestForm)}
                className="bg-emerald-600 hover:bg-emerald-500 border-none text-white font-black italic uppercase px-8 py-4 rounded-2xl flex items-center gap-2 shadow-lg hover:shadow-emerald-500/20 hover:scale-105 transition-all"
              >
                {showIngestForm ? (
                  t('labs.seiyuu.close_panel', 'Fermer le panel')
                ) : (
                  <>
                    <Plus className="w-5 h-5" />{' '}
                    {t('labs.seiyuu.youtube_ingest', 'Ingestion YouTube')}
                  </>
                )}
              </Button>
            </div>
          </header>

          {/* Ingestion Panel */}
          <AnimatePresence>
            {showIngestForm && (
              <SeiyuuIngestFormPanel
                ingestName={ingestName}
                setIngestName={setIngestName}
                ingestLang={ingestLang}
                setIngestLang={setIngestLang}
                ingestSource={ingestSource}
                setIngestSource={setIngestSource}
                ingestDef={ingestDef}
                setIngestDef={setIngestDef}
                ingestRoles={ingestRoles}
                setIngestRoles={setIngestRoles}
                ingestError={ingestError}
                ingestSuccess={ingestSuccess}
                isPending={ingestMutation.isPending}
                onCancel={() => setShowIngestForm(false)}
                onSubmit={handleIngestSubmit}
              />
            )}
          </AnimatePresence>

          {/* Search Bar & Filters */}
          <SeiyuuSearchFiltersPanel
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            langFilter={langFilter}
            setLangFilter={setLangFilter}
            originFilter={originFilter}
            setOriginFilter={setOriginFilter}
            isLoading={isLoading}
            isRefetching={isRefetching}
            onSearch={handleSearch}
          />

          {/* Results Area */}
          <div className="grid grid-cols-1 gap-12">
            <AnimatePresence mode="wait">
              {data?.results && data.results.length > 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="grid grid-cols-1 lg:grid-cols-2 gap-8"
                >
                  {data.results.map((seiyuu, i) => (
                    <SeiyuuResultCard
                      key={seiyuu.name}
                      seiyuu={seiyuu}
                      index={i}
                      activeAudio={activeAudio}
                      audioLoading={audioLoading}
                      onPlaySample={playSample}
                    />
                  ))}
                </motion.div>
              ) : data && searchQuery ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="py-32 text-center border-4 border-dashed border-white/5 rounded-[4rem]"
                >
                  <Info className="w-20 h-24 mx-auto mb-8 text-white/10" />
                  <h3 className="text-4xl font-black italic uppercase manga-font text-white/20">
                    {t('labs.seiyuu.no_profile_found', 'Aucun profil trouvé')}
                  </h3>
                  <p className="text-sm font-bold uppercase tracking-[0.4em] text-white/10">
                    {t(
                      'labs.seiyuu.try_youtube_ingest',
                      'Essayez de lancer une ingestion depuis YouTube !',
                    )}
                  </p>
                </motion.div>
              ) : (
                !isLoading &&
                !isRefetching && (
                  <div className="py-32 text-center opacity-10 flex flex-col items-center border-4 border-dashed border-white/5 rounded-[4rem]">
                    <Music className="w-32 h-32 mb-12" />
                    <h3 className="text-5xl font-black italic uppercase manga-font mb-4">
                      Neural Vocal Base
                    </h3>
                    <p className="text-lg font-bold uppercase tracking-[0.4em]">
                      Prêt pour l'indexation sémantique des fréquences.
                    </p>
                  </div>
                )
              )}
            </AnimatePresence>
          </div>

          {/* Guide & Protocole */}
          <SeiyuuGuideProtocolSection />
        </div>
      </AnimatedPage>
    </div>
  );
};

export default SeiyuuDiscoveryPage;
