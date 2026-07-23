import React, { useState } from 'react';
import { Mic, Play, Save, Wand2, Search, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../utils/apiClient';
import { motion, AnimatePresence } from 'framer-motion';
import { VoiceProfile } from '../../types';
import { useToastStore } from '../../store/toastStore';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_BTN_GHOST,
} from './components/shared/LabKit';

/** Action principale compacte (même voix que LAB_CTA, sans w-full). */
const CTA_COMPACT =
  'inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl border-none bg-[#E8442B] px-8 py-4 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50';

const MangaVoicePage: React.FC = () => {
  const { t } = useTranslation();
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingAudio, setLoadingAudio] = useState<boolean>(false);
  const [text, setText] = useState<string>('');
  const [character, setCharacter] = useState<string>('Naruto Uzumaki');
  const [refAudio, setRefAudio] = useState<File | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<VoiceProfile | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  // Search & Filter state for casting
  const [searchQuery, setSearchQuery] = useState('');
  const [langFilter, setLangFilter] = useState('');

  // Fetch Voice Profiles
  const { data: profilesData, isLoading: isLoadingProfiles } = useQuery<{
    results: VoiceProfile[];
  }>({
    queryKey: ['voice-profiles-manga', searchQuery, langFilter],
    queryFn: () => {
      let url = `/api/v1/labs/audio/seiyuu/?q=${encodeURIComponent(searchQuery)}`;
      if (langFilter) url += `&language=${langFilter}`;
      return apiClient(url);
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setRefAudio(file);
      setSelectedProfile(null);
      setCharacter(file.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleSelectProfile = async (profile: VoiceProfile) => {
    setSelectedProfile(profile);
    setCharacter(profile.name);
    setLoadingAudio(true);

    try {
      const resp = await fetch(profile.sample_url);
      if (resp.ok) {
        const blob = await resp.blob();
        const file = new File([blob], `${profile.name}_sample.wav`, { type: 'audio/wav' });
        setRefAudio(file);
      } else {
        useToastStore.getState().addToast("Échec du chargement de l'échantillon vocal.", 'error');
      }
    } catch (err) {
      console.error('Failed to load reference audio from profile:', err);
      useToastStore.getState().addToast("Échec du chargement de l'échantillon vocal.", 'error');
    } finally {
      setLoadingAudio(false);
    }
  };

  const handleGenerate = async () => {
    if (!text || !refAudio) return;
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('text', text);
      formData.append('character', character);
      formData.append('reference_audio', refAudio);

      const data = await apiClient('/api/v1/labs/manga-voice/', {
        method: 'POST',
        body: formData,
        headers: {},
      });

      setAudioUrl(data.audio_data);
    } catch (err) {
      console.error(err);
      useToastStore.getState().addToast('Échec de la génération de la voix.', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Dubbing"
        title="Manga voice"
        accent="lab"
        lede={t(
          'labs.manga_voice.subtitle',
          'Donnez vie à vos planches avec le doublage IA zero-shot et le clonage vocal instantané.',
        )}
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Casting Panel (Left) */}
        <LabPanel
          title={t('labs.manga_voice.casting_title', 'Casting Vocal')}
          className="h-fit lg:col-span-4"
        >
          <div className="space-y-6">
            <p className="text-sm leading-relaxed text-[#8F94A5]">
              {t(
                'labs.manga_voice.casting_desc',
                'Choisissez une voix de la BDD ou chargez votre propre extrait.',
              )}
            </p>

            {/* Language filter tab */}
            <div className="flex gap-1 rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-1">
              {[
                { label: t('labs.manga_voice.filter_all', 'Tous'), value: '' },
                { label: t('labs.manga_voice.filter_japanese', 'Seiyuu (JP)'), value: 'japanese' },
                { label: t('labs.manga_voice.filter_french', 'VF (FR)'), value: 'french' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setLangFilter(opt.value)}
                  className={`flex-1 cursor-pointer rounded-lg border-none py-2 text-[9px] font-black uppercase tracking-wider transition-colors ${
                    langFilter === opt.value
                      ? 'bg-[#FDB913]/10 text-[#FDB913]'
                      : 'bg-transparent text-[#8F94A5] hover:text-[#F4F1E8]'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            {/* Quick Search */}
            <div className="relative">
              <Search
                className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8F94A5]"
                aria-hidden="true"
              />
              <input
                type="text"
                placeholder={t('labs.manga_voice.search_placeholder', 'Rechercher une voix...')}
                aria-label={t('labs.manga_voice.search_placeholder', 'Rechercher une voix...')}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`${LAB_INPUT} pl-10 text-xs`}
              />
            </div>

            {/* Profiles List */}
            <div className="custom-scrollbar max-h-[350px] space-y-2 overflow-y-auto pr-1">
              {isLoadingProfiles ? (
                <div className="py-10 text-center">
                  <Loader2 className="mx-auto h-6 w-6 animate-spin text-[#FDB913]" />
                </div>
              ) : profilesData?.results && profilesData.results.length > 0 ? (
                profilesData.results.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => handleSelectProfile(p)}
                    className={`flex w-full cursor-pointer items-center justify-between rounded-xl border px-4 py-3.5 text-left text-xs font-black transition-colors ${
                      selectedProfile?.id === p.id
                        ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#F4F1E8]'
                        : 'border-[#F4F1E8]/10 bg-[#0B0C10] text-[#8F94A5] hover:border-[#F4F1E8]/25 hover:text-[#F4F1E8]'
                    }`}
                  >
                    <div className="flex flex-col gap-0.5 truncate pr-2">
                      <span className="truncate">{p.name}</span>
                      <span className="truncate text-[8px] font-medium uppercase tracking-wide text-[#8F94A5]">
                        {p.roles || 'Doubleur'}
                      </span>
                    </div>
                    <span className="flex-none text-[8px] font-black uppercase tracking-widest text-[#8F94A5]">
                      {p.language === 'japanese'
                        ? '🇯🇵 JP'
                        : p.language === 'french'
                          ? '🇫🇷 FR'
                          : '🌐'}
                    </span>
                  </button>
                ))
              ) : (
                <div className="py-10 text-center">
                  <span className="text-[10px] font-black uppercase text-[#8F94A5]">
                    {t('labs.manga_voice.no_voice_found', 'Aucune voix trouvée')}
                  </span>
                </div>
              )}
            </div>

            <div className="space-y-4 border-t border-[#F4F1E8]/10 pt-6">
              <h4 className={LAB_LABEL}>
                {t('labs.manga_voice.manual_load_title', 'Ou charger manuellement')}
              </h4>
              <button
                type="button"
                className={`${LAB_BTN_GHOST} w-full justify-center`}
                onClick={() => document.getElementById('audio-upload')?.click()}
              >
                <Mic className="h-4 w-4" aria-hidden="true" />{' '}
                {refAudio && !selectedProfile
                  ? t('labs.manga_voice.manual_voice_loaded', 'VOIX MANUELLE CHARGÉE')
                  : t('labs.manga_voice.load_file_btn', 'CHARGER UN WAV/MP3')}
              </button>
              <input
                type="file"
                id="audio-upload"
                className="hidden"
                accept="audio/*"
                onChange={handleFileChange}
                aria-label={t(
                  'labs.manga_voice.load_file_aria',
                  'Charger un fichier audio de référence',
                )}
              />
              {refAudio && (
                <div className="flex items-center justify-between rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3 text-xs font-bold">
                  <span className="max-w-[200px] truncate text-[#8F94A5]">{refAudio.name}</span>
                  {loadingAudio ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-[#FDB913]" />
                  ) : (
                    <span className="text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                      {t('labs.manga_voice.ready', 'PRÊT')}
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        </LabPanel>

        {/* Dialog and Result Area (Right) */}
        <div className="space-y-8 lg:col-span-8">
          <LabPanel title={t('labs.manga_voice.script_title', 'Script du Dialogue')}>
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              aria-label={t('labs.manga_voice.script_title', 'Script du dialogue')}
              placeholder={
                refAudio
                  ? t(
                      'labs.manga_voice.script_placeholder',
                      'Entrez le texte que {{character}} doit dire...',
                      { character },
                    )
                  : t(
                      'labs.manga_voice.script_placeholder_select',
                      "Sélectionnez d'abord un doubleur dans le menu de gauche...",
                    )
              }
              disabled={!refAudio}
              className={`${LAB_INPUT} h-40 resize-none`}
            />
            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={handleGenerate}
                disabled={!text || !refAudio || loading || loadingAudio}
                className={CTA_COMPACT}
              >
                {loading ? (
                  <Wand2 className="h-5 w-5 animate-spin" aria-hidden="true" />
                ) : (
                  t('labs.manga_voice.generate_dubbing', 'GÉNÉRER LE DUBBING')
                )}
              </button>
            </div>
          </LabPanel>

          <AnimatePresence>
            {audioUrl && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9 }}
              >
                <LabPanel
                  title={t('labs.manga_voice.dubbing_complete', 'Dubbing Terminé')}
                  corner="Conversion RVC v2"
                >
                  <div className="flex flex-col items-center gap-6 text-center">
                    <div className="flex h-20 w-20 items-center justify-center rounded-full bg-[#FDB913] text-[#0B0C10]">
                      <Play className="ml-1 h-8 w-8" aria-hidden="true" />
                    </div>

                    <p className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
                      {t(
                        'labs.manga_voice.character_ready',
                        'Le personnage de {{character}} est prêt à parler.',
                        { character },
                      )}
                    </p>

                    <audio
                      controls
                      src={audioUrl}
                      className="w-full max-w-xl"
                      aria-label="Lecteur audio du doublage généré"
                    >
                      <track kind="captions" />
                    </audio>

                    <div className="flex flex-wrap justify-center gap-4">
                      <button type="button" className={LAB_BTN_GHOST}>
                        <Save className="h-4 w-4" aria-hidden="true" />{' '}
                        {t('labs.manga_voice.save', 'SAUVEGARDER')}
                      </button>
                      <button type="button" className={CTA_COMPACT}>
                        {t('labs.manga_voice.inject_btn', 'INJECTER DANS LA PLANCHE')}
                      </button>
                    </div>
                  </div>
                </LabPanel>
              </motion.div>
            )}
          </AnimatePresence>

          {!audioUrl && !loading && (
            <LabEmpty
              icon={<Mic className="h-16 w-16" aria-hidden="true" />}
              title={t('labs.manga_voice.waiting_generation', 'En attente de génération')}
              hint="Choisis une voix dans le casting, écris la réplique, puis lance la génération : le doublage apparaîtra ici."
            />
          )}
        </div>
      </div>

      {/* Guide & Protocole */}
      <LabGuide
        steps={[
          {
            title: 'Le casting',
            body: t(
              'labs.manga_voice.guide_casting_desc',
              'Choisissez un doubleur dans le catalogue (filtrable par langue JP/FR) ou chargez votre propre extrait WAV/MP3 comme voix de référence.',
            ),
          },
          {
            title: 'Le script',
            body: t(
              'labs.manga_voice.guide_script_desc',
              'Écrivez la réplique que le personnage doit dire, puis lancez la génération : la voix choisie prononce votre texte.',
            ),
          },
          {
            title: 'Le résultat',
            body: t(
              'labs.manga_voice.guide_result_desc',
              'Écoutez le doublage dans le lecteur intégré : idéal pour donner de la voix à une planche de manga ou tester un casting.',
            ),
          },
        ]}
        note={`${t(
          'labs.manga_voice.guide_footer_1',
          "Clonage vocal zero-shot : le texte et un échantillon audio de référence sont envoyés à l'endpoint manga-voice, qui conditionne la synthèse vocale sur ce timbre sans entraînement préalable.",
        )} ${t(
          'labs.manga_voice.guide_footer_2',
          "Les profils du catalogue fournissent l'échantillon automatiquement ; la sortie est affinée via conversion RVC v2.",
        )}`}
      />
    </LabPage>
  );
};

export default MangaVoicePage;
