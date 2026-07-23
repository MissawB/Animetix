import React, { useState, useEffect } from 'react';
import { Search, ArrowRight, Plus } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useTranslation } from 'react-i18next';
import { useAudioLab } from '../../features/labs/hooks/useAudioLab';
import { useQuickIngestForm } from '../../features/labs/hooks/useQuickIngestForm';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { LabPage, LabHeader, LAB_INPUT, LAB_BTN_GHOST } from './components/shared/LabKit';
import { VoiceProfile } from '../../types';
import type { AudioProcessPayload } from '../../features/labs/services/audioLabService';
import { useToastStore } from '../../store/toastStore';
import { AudioLabRecordingPanel, type Recording } from './components/AudioLabRecordingPanel';
import { AudioLabSynthesisForm, type AudioFormValues } from './components/AudioLabSynthesisForm';
import { AudioLabQuickIngestPanel } from './components/AudioLabQuickIngestPanel';
import { SeiyuuProfileCard } from './components/SeiyuuProfileCard';
import { AudioLabGuideSection } from './components/AudioLabGuideSection';

interface VoiceCloningPayload {
  text: string;
  audio_file: File | null;
  source_type: 'upload' | 'library';
}

const AudioLabPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const audioSchema = React.useMemo(
    () =>
      z.object({
        text: z
          .string()
          .min(
            10,
            t(
              'labs.audio.text_validation',
              'Veuillez entrer au moins 10 caractères pour la synthèse.',
            ),
          )
          .max(500, t('labs.audio.text_too_long', 'Le texte est trop long.')),
      }),
    [t],
  );

  const {
    data,
    loading,
    processAudio,
    searchSeiyuu,
    ingestVoice,
    seiyuuResults,
    isSearchingSeiyuu,
    isIngestingVoice,
  } = useAudioLab();

  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [seiyuuQuery, setSeiyuuQuery] = useState('');
  const [langFilter, setLangFilter] = useState('');
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [selectedSeiyuu, setSelectedSeiyuu] = useState<VoiceProfile | null>(null);
  const [activeAudio, setActiveAudio] = useState<string | null>(null);
  const [audioLoading, setAudioLoading] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<AudioFormValues>({
    resolver: zodResolver(audioSchema),
    defaultValues: { text: '' },
  });

  // Fetch initial profiles list
  useEffect(() => {
    searchSeiyuu('', langFilter);
  }, [searchSeiyuu, langFilter]);

  const startRecording = () => setIsRecording(true);
  const stopRecording = () => {
    setIsRecording(false);
    setSelectedSeiyuu(null);
    setRecordings([
      ...recordings,
      { id: Date.now(), name: `Extrait #${recordings.length + 1}`, duration: '0:12' },
    ]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioFile(file);
      setSelectedSeiyuu(null);
      setRecordings([{ id: Date.now(), name: file.name, duration: 'N/A' }]);
    }
  };

  const onDragStart = (e: React.DragEvent, seiyuu: VoiceProfile) => {
    e.dataTransfer.setData('seiyuu', JSON.stringify(seiyuu));
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(true);
  };

  const onDragLeave = () => {
    setIsDraggingOver(false);
  };

  const selectVoiceProfile = async (seiyuu: VoiceProfile) => {
    setSelectedSeiyuu(seiyuu);
    setRecordings([
      {
        id: Date.now(),
        name: t('labs.audio.recording_voice_of', {
          name: seiyuu.name,
          defaultValue: 'Voix de {{name}}',
        }),
        duration: t('labs.audio.recording_sample_db', 'Sample BDD'),
      },
    ]);

    // Fetch the sample and convert to File to satisfy the existing backend.
    // NB: sample_url is a media asset (Django FileField .url) that may be a
    // cross-origin GCS/HF/YouTube URL, and the body is a binary blob — not JSON.
    // So we use a raw fetch here on purpose: routing it through apiClient would
    // attach the user's Firebase token/CSRF to a third-party host and try to
    // JSON-parse the audio. We still surface failures via a toast.
    try {
      setAudioLoading(seiyuu.sample_url);
      const resp = await fetch(seiyuu.sample_url);
      if (resp.ok) {
        const blob = await resp.blob();
        const file = new File([blob], `${seiyuu.name}_sample.wav`, { type: 'audio/wav' });
        setAudioFile(file);
      } else {
        useToastStore
          .getState()
          .addToast(
            t(
              'labs.audio.recording_error_load_sample',
              "Échec du chargement de l'échantillon vocal.",
            ),
            'error',
          );
      }
      setAudioLoading(null);
    } catch {
      useToastStore
        .getState()
        .addToast(
          t(
            'labs.audio.recording_error_load_sample',
            "Échec du chargement de l'échantillon vocal.",
          ),
          'error',
        );
      setAudioLoading(null);
    }
  };

  const quickIngest = useQuickIngestForm({
    ingestVoice,
    onIngested: (profile) => {
      selectVoiceProfile(profile);
      searchSeiyuu(seiyuuQuery, langFilter); // refresh the list
    },
  });

  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
    const seiyuuData = e.dataTransfer.getData('seiyuu');
    if (seiyuuData) {
      const seiyuu = JSON.parse(seiyuuData) as VoiceProfile;
      selectVoiceProfile(seiyuu);
    }
  };

  const onSubmit = async (values: AudioFormValues) => {
    const payload: VoiceCloningPayload = {
      text: values.text,
      audio_file: audioFile,
      source_type: audioFile ? 'upload' : 'library',
    };
    await processAudio(payload as unknown as AudioProcessPayload);
  };

  const playResult = () => {
    if (data?.audio_url) {
      const audio = new Audio(data.audio_url);
      audio.play();
    }
  };

  const playProfileSample = (url: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (activeAudio === url) {
      setActiveAudio(null);
      return;
    }
    const audio = new Audio(url);
    audio.play().catch((err) => console.error(err));
    setActiveAudio(url);
    audio.onended = () => setActiveAudio(null);
  };

  if (loading)
    return (
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <CardSkeleton />
        </div>
      </div>
    );

  return (
    <LabPage wide>
      <LabHeader
        code="Protocole · Audio"
        title="Forge"
        accent="vocale"
        lede="Clone une voix à partir d'un court échantillon : choisis un profil du catalogue seiyuu/VF, importe un extrait ou enregistre-toi, puis fais-lui dire ton texte."
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Main Recording & Cloning Area (Left & Center) */}
        <div className="lg:col-span-8 space-y-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Recording Panel */}
            <div className="md:col-span-1">
              <AudioLabRecordingPanel
                isRecording={isRecording}
                selectedSeiyuu={selectedSeiyuu}
                audioLoading={audioLoading}
                recordings={recordings}
                startRecording={startRecording}
                stopRecording={stopRecording}
                onFileChange={handleFileChange}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
                onClearRecordings={() => {
                  setRecordings([]);
                  setAudioFile(null);
                  setSelectedSeiyuu(null);
                }}
                isDraggingOver={isDraggingOver}
              />
            </div>

            {/* Cloning Panel */}
            <div className="md:col-span-2 space-y-8">
              <AudioLabSynthesisForm
                register={register}
                handleSubmit={handleSubmit}
                errors={errors}
                onSubmit={onSubmit}
                selectedSeiyuu={selectedSeiyuu}
                disabled={recordings.length === 0 && !audioFile}
                audioUrl={data?.audio_url}
                playResult={playResult}
              />
            </div>
          </div>
        </div>

        {/* Sidebar Seiyuu / Doubleur Database */}
        <aside className="lg:col-span-4 space-y-8">
          <div className="space-y-4">
            <div className="flex justify-between items-end gap-4">
              <div className="space-y-1">
                <h2 className="font-manga text-2xl font-black italic uppercase tracking-tight text-[#F4F1E8] flex items-center gap-2">
                  Voice <span className="text-[#E8442B]">Database</span>
                </h2>
                <p className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  {t('labs.audio.sidebar_subtitle', 'Catalogue Seiyuu & VF.')}
                </p>
              </div>
              <button
                type="button"
                className="group mb-1 inline-flex items-center gap-1 border-none bg-transparent p-0 text-[9px] font-black uppercase tracking-widest text-[#FDB913] transition-colors hover:text-[#F4F1E8] cursor-pointer"
                onClick={() => navigate('/lab/audio/seiyuu/')}
              >
                {t('labs.audio.sidebar_fullscreen', 'Plein écran')}{' '}
                <ArrowRight className="w-3 h-3 inline group-hover:translate-x-1 transition-transform" />
              </button>
            </div>

            {/* Quick Ingest Toggle */}
            <button
              type="button"
              onClick={quickIngest.toggle}
              className={`${LAB_BTN_GHOST} w-full justify-center rounded-xl border-dashed py-3.5 text-[9px]`}
            >
              <Plus className="w-3 h-3" />{' '}
              {t('labs.audio.sidebar_quick_ingest', 'Ingestion YouTube rapide')}
            </button>

            {/* Ingestion Panel inside Sidebar */}
            <AudioLabQuickIngestPanel
              quickIngest={quickIngest}
              isIngestingVoice={isIngestingVoice}
            />

            {/* Language filter tab */}
            <div className="flex gap-1.5 rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] p-1">
              {[
                { label: t('labs.audio.filter_all', 'Tous'), value: '' },
                { label: t('labs.audio.filter_japanese', 'Seiyuu (JP)'), value: 'japanese' },
                { label: t('labs.audio.filter_french', 'VF (FR)'), value: 'french' },
              ].map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setLangFilter(opt.value)}
                  className={`flex-1 cursor-pointer py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-colors ${
                    langFilter === opt.value
                      ? 'bg-[#FDB913]/10 text-[#FDB913] border border-[#FDB913]/25'
                      : 'bg-transparent text-[#8F94A5] hover:text-[#F4F1E8] border border-transparent'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#8F94A5]" />
              <input
                type="text"
                placeholder={t('labs.audio.search_placeholder', 'Seiyuu ou personnage...')}
                aria-label={t('labs.audio.search_aria', 'Rechercher un seiyuu ou un personnage')}
                value={seiyuuQuery}
                onChange={(e) => {
                  setSeiyuuQuery(e.target.value);
                  searchSeiyuu(e.target.value, langFilter);
                }}
                className={`${LAB_INPUT} pl-12`}
              />
              {isSearchingSeiyuu && (
                <div className="absolute right-4 top-1/2 -translate-y-1/2 w-3 h-3 border-2 border-[#FDB913] border-t-transparent rounded-full animate-spin" />
              )}
            </div>
          </div>

          <div className="space-y-6 max-h-[800px] overflow-y-auto pr-2 custom-scrollbar">
            {seiyuuResults.map((s: VoiceProfile, idx: number) => (
              <SeiyuuProfileCard
                key={idx}
                seiyuu={s}
                isSelected={selectedSeiyuu?.id === s.id}
                onSelect={() => selectVoiceProfile(s)}
                onDragStart={(e) => onDragStart(e, s)}
                onPlaySample={(e) => playProfileSample(s.sample_url, e)}
              />
            ))}

            {seiyuuResults.length === 0 && !isSearchingSeiyuu && (
              <div className="py-20 text-center text-[#8F94A5]">
                <Search className="w-8 h-8 mx-auto mb-4" />
                <p className="text-[10px] font-black uppercase tracking-widest">
                  {t('labs.audio.search_no_results', 'Aucun résultat')}
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>

      {/* Guide & Protocole */}
      <AudioLabGuideSection />
    </LabPage>
  );
};

export default AudioLabPage;
