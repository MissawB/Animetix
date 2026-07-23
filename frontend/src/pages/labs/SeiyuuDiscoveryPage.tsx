import React, { useState } from 'react';
import { Plus, Info, Music } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../utils/apiClient';
import { motion, AnimatePresence } from 'framer-motion';
import type { IngestVoicePayload } from '../../features/labs/services/audioLabService';
import type { SeiyuuApiResponse } from '../../features/labs/types/seiyuuTypes';
import { LabPage, LabHeader, LabEmpty } from './components/shared/LabKit';

import { SeiyuuIngestFormPanel } from './components/SeiyuuIngestFormPanel';
import { SeiyuuSearchFiltersPanel } from './components/SeiyuuSearchFiltersPanel';
import { SeiyuuResultCard } from './components/SeiyuuResultCard';
import { SeiyuuGuideProtocolSection } from './components/SeiyuuGuideProtocolSection';

/** Action principale compacte (même voix que LAB_CTA, sans w-full). */
const CTA_COMPACT =
  'inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl border-none bg-[#E8442B] px-8 py-3.5 font-manga text-sm font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50';

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
    <LabPage>
      <LabHeader
        code="Protocole · Seiyuu"
        title="SEIYUU"
        accent="DISCOVERY"
        lede={t(
          'labs.seiyuu.subtitle',
          'Explorez les voix cultes (Seiyuus & Doubleurs) et ingérez de nouvelles voix à la volée.',
        )}
      />

      {/* Ingestion toggle */}
      <div className="mb-8 flex justify-end">
        <button
          type="button"
          onClick={() => setShowIngestForm(!showIngestForm)}
          className={CTA_COMPACT}
        >
          {showIngestForm ? (
            t('labs.seiyuu.close_panel', 'Fermer le panel')
          ) : (
            <>
              <Plus className="h-5 w-5" aria-hidden="true" />{' '}
              {t('labs.seiyuu.youtube_ingest', 'Ingestion YouTube')}
            </>
          )}
        </button>
      </div>

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
              className="grid grid-cols-1 gap-8 lg:grid-cols-2"
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
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <LabEmpty
                icon={<Info className="h-16 w-16" aria-hidden="true" />}
                title={t('labs.seiyuu.no_profile_found', 'Aucun profil trouvé')}
                hint={t(
                  'labs.seiyuu.try_youtube_ingest',
                  'Essayez de lancer une ingestion depuis YouTube !',
                )}
              />
            </motion.div>
          ) : (
            !isLoading &&
            !isRefetching && (
              <LabEmpty
                icon={<Music className="h-16 w-16" aria-hidden="true" />}
                title="Base vocale en veille"
                hint="Cherche un doubleur ou un personnage pour explorer le catalogue — ou ingère une nouvelle voix depuis YouTube."
              />
            )
          )}
        </AnimatePresence>
      </div>

      {/* Guide & Protocole */}
      <SeiyuuGuideProtocolSection />
    </LabPage>
  );
};

export default SeiyuuDiscoveryPage;
