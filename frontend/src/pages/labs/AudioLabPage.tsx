import React, { useState, useEffect } from 'react';
import {
  Mic,
  MicOff,
  Play,
  Save,
  Trash2,
  Wand2,
  Search,
  Star,
  User,
  ArrowRight,
  Plus,
  Video,
  Loader2,
  Volume2,
} from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { useAudioLab } from '../../features/labs/hooks/useAudioLab';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { CardSkeleton } from "../../components/ui/Skeleton";
import { VoiceProfile } from '../../types';
import type { AudioProcessPayload } from '../../features/labs/services/audioLabService';
import { useToastStore } from '../../store/toastStore';

const audioSchema = z.object({
  text: z.string().min(10, "Veuillez entrer au moins 10 caractères pour la synthèse.").max(500, "Le texte est trop long."),
});

type AudioFormValues = z.infer<typeof audioSchema>;

interface Recording {
  id: number;
  name: string;
  duration: string;
}

interface VoiceCloningPayload {
  text: string;
  audio_file: File | null;
  source_type: 'upload' | 'library';
}

const AudioLabPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
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

  // Quick Ingestion Mode
  const [showQuickIngest, setShowQuickIngest] = useState(false);
  const [quickName, setQuickName] = useState('');
  const [quickLang, setQuickLang] = useState('japanese');
  const [quickSource, setQuickSource] = useState('');
  const [quickError, setQuickError] = useState('');

  const { register, handleSubmit, formState: { errors } } = useForm<AudioFormValues>({
    resolver: zodResolver(audioSchema),
    defaultValues: { text: '' }
  });

  // Fetch initial profiles list
  useEffect(() => {
    searchSeiyuu('', langFilter);
  }, [searchSeiyuu, langFilter]);

  const startRecording = () => setIsRecording(true);
  const stopRecording = () => {
    setIsRecording(false);
    setSelectedSeiyuu(null);
    setRecordings([...recordings, { id: Date.now(), name: `Extrait #${recordings.length + 1}`, duration: '0:12' }]);
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
    setRecordings([{ id: Date.now(), name: `Voix de ${seiyuu.name}`, duration: 'Sample BDD' }]);

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
        useToastStore.getState().addToast("Échec du chargement de l'échantillon vocal.", 'error');
      }
      setAudioLoading(null);
    } catch {
      useToastStore.getState().addToast("Échec du chargement de l'échantillon vocal.", 'error');
      setAudioLoading(null);
    }
  };

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
    audio.play().catch(err => console.error(err));
    setActiveAudio(url);
    audio.onended = () => setActiveAudio(null);
  };

  const handleQuickIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    setQuickError('');
    if (!quickName || !quickSource) {
      setQuickError("Le nom et la source sont requis.");
      return;
    }
    try {
      const response = await ingestVoice({
        name: quickName,
        language: quickLang,
        query: quickSource,
      });
      // Select the newly created voice profile
      selectVoiceProfile(response.profile);
      setShowQuickIngest(false);
      setQuickName('');
      setQuickSource('');
      // Refresh list
      searchSeiyuu(seiyuuQuery, langFilter);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : '';
      setQuickError(message || "Erreur d'ingestion.");
    }
  };

  if (loading) return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <CardSkeleton />
    </div>
  );

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-16">
      <header className="mb-12">
        <h1 className="text-6xl font-black italic manga-font mb-4 tracking-tighter uppercase">
          {t('labs.audio.title')}
        </h1>
        <p className="text-gray-500 font-bold uppercase tracking-widest">{t('labs.audio.cloning')}</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Main Recording & Cloning Area (Left & Center) */}
        <div className="lg:col-span-8 space-y-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Recording Panel */}
            <div className="md:col-span-1">
              <Card
                padding="lg"
                className={`h-fit transition-all duration-300 ${isDraggingOver ? 'ring-4 ring-blue-500 bg-blue-500/10 scale-105' : ''}`}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
              >
                <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                  <Mic className="w-4 h-4" /> Source Vocale
                </h3>

                <div className="flex flex-col items-center py-6">
                  <button
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`w-24 h-24 rounded-full flex items-center justify-center transition-all shadow-2xl relative ${isRecording ? 'bg-red-500 animate-pulse scale-110' : selectedSeiyuu ? 'bg-blue-600 text-white' : 'bg-black text-white hover:scale-105'}`}
                    aria-label={isRecording ? 'Arrêter l\'enregistrement' : 'Démarrer l\'enregistrement'}
                  >
                    {audioLoading ? (
                      <Loader2 className="w-8 h-8 animate-spin" />
                    ) : isRecording ? (
                      <MicOff className="w-8 h-8" />
                    ) : selectedSeiyuu ? (
                      <Star className="w-8 h-8 fill-current text-yellow-400" />
                    ) : (
                      <Mic className="w-8 h-8" />
                    )}
                  </button>
                  <span className={`mt-6 font-black italic uppercase tracking-widest text-[9px] ${isRecording ? 'text-red-500' : selectedSeiyuu ? 'text-blue-500' : 'opacity-40'}`}>
                    {audioLoading ? 'Chargement voix...' : isRecording ? 'Enregistrement...' : selectedSeiyuu ? `Voix: ${selectedSeiyuu.name}` : 'Prêt à enregistrer'}
                  </span>
                  {selectedSeiyuu && (
                    <p className="text-[7px] font-bold uppercase opacity-30 mt-1">Glissez un autre seiyuu pour changer</p>
                  )}
                </div>

                <div className="relative mb-6">
                  <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-black/5 dark:border-white/5"></div></div>
                  <div className="relative flex justify-center text-[9px] uppercase font-black"><span className="px-2 bg-white dark:bg-navy-800 text-gray-400">ou</span></div>
                </div>

                <Button
                  variant="outline"
                  fullWidth
                  onClick={() => document.getElementById('audio-upload')?.click()}
                  className="text-[10px] py-3"
                >
                  Importer .wav
                </Button>
                <input type="file" id="audio-upload" className="hidden" accept=".wav,.mp3" onChange={handleFileChange} aria-label="Importer un fichier audio" />

                <div className="mt-8 space-y-3">
                  {recordings.map((rec) => (
                    <div key={rec.id} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl flex items-center justify-between group">
                      <div className="flex items-center gap-2">
                        <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-white ${selectedSeiyuu ? 'bg-blue-600' : 'bg-blue-500'}`}>
                          <Play className="w-3 h-3 fill-current" />
                        </div>
                        <span className="font-bold text-[9px] truncate max-w-[80px]">{rec.name}</span>
                      </div>
                      <button
                        type="button"
                        aria-label="Supprimer l'enregistrement"
                        className="p-1 hover:bg-red-500/10 rounded transition-all opacity-0 group-hover:opacity-100 border-none bg-transparent cursor-pointer"
                        onClick={() => { setRecordings([]); setAudioFile(null); setSelectedSeiyuu(null); }}
                      >
                        <Trash2 className="w-3 h-3 text-red-500" />
                      </button>
                    </div>
                  ))}
                </div>
              </Card>
            </div>

            {/* Cloning Panel */}
            <div className="md:col-span-2 space-y-8">
              <Card padding="lg" className="relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-5">
                  <Wand2 className="w-40 h-42 text-purple-500" />
                </div>

                <h3 className="text-3xl font-black italic manga-font mb-8">FORGE <span className="text-purple-500">VOCALE</span></h3>

                <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-8">
                  <div className="flex flex-col gap-2">
                    <textarea
                      {...register('text')}
                      className={`w-full p-8 rounded-[2rem] bg-gray-50 dark:bg-gray-800 outline-none font-medium text-lg min-h-[200px] transition-all 
                                        ${errors.text ? 'ring-2 ring-red-500' : 'focus:ring-2 focus:ring-purple-500'}
                                    `}
                      placeholder={selectedSeiyuu ? `Faites parler ${selectedSeiyuu.name}...` : "Tapez le texte que l'IA doit dire avec votre voix..."}
                    ></textarea>
                    {errors.text && <span className="text-red-500 text-xs font-black pl-4">{errors.text.message}</span>}
                  </div>

                  <Button
                    type="submit"
                    variant="primary"
                    size="lg"
                    fullWidth
                    disabled={(recordings.length === 0 && !audioFile)}
                    className="bg-gradient-to-r from-purple-600 to-blue-600 border-none py-6 animate-pulse"
                  >
                    <Save className="w-6 h-6 mr-2" /> {selectedSeiyuu ? `Synthétiser ${selectedSeiyuu.name}` : t('labs.audio.generate')}
                  </Button>
                </form>
              </Card>

              {data?.audio_url && (
                <div className="bg-green-500/10 border-2 border-green-500 p-8 rounded-[2.5rem] flex items-center justify-between animate-slide-up">
                  <div>
                    <h4 className="font-black text-green-500 italic text-xl uppercase leading-none mb-1">RÉSULTAT PRÊT !</h4>
                    <p className="font-bold opacity-60 text-sm">Votre voix a été synthétisée avec succès.</p>
                  </div>
                  <Button
                    variant="success"
                    className="p-4 rounded-2xl"
                    onClick={playResult}
                  >
                    <Play className="w-6 h-6 fill-current" />
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar Seiyuu / Doubleur Database */}
        <aside className="lg:col-span-4 space-y-8">
          <div className="space-y-4">
            <div className="flex justify-between items-end gap-4">
              <div className="space-y-1">
                <h2 className="text-2xl font-black italic manga-font uppercase flex items-center gap-2">
                  Voice <span className="text-blue-500">Database</span>
                </h2>
                <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Catalogue Seiyuu & VF.</p>
              </div>
              <Button
                variant="ghost"
                className="p-0 text-[9px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 transition-colors group mb-1"
                onClick={() => navigate('/lab/audio/seiyuu/')}
              >
                Plein Écran <ArrowRight className="w-3 h-3 inline group-hover:translate-x-1 transition-transform" />
              </Button>
            </div>

            {/* Quick Ingest Toggle */}
            <Button
              variant="outline"
              fullWidth
              onClick={() => setShowQuickIngest(!showQuickIngest)}
              className="text-[9px] uppercase font-black tracking-wider flex items-center justify-center gap-1.5 py-3.5 border-dashed border-blue-500/30 text-blue-400 hover:bg-blue-500/10"
            >
              <Plus className="w-3 h-3" /> Ingestion YouTube Rapide
            </Button>

            {/* Ingestion Panel inside Sidebar */}
            <AnimatePresence>
              {showQuickIngest && (
                <motion.form
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  onSubmit={handleQuickIngest}
                  className="bg-navy-950/80 border border-blue-500/20 p-5 rounded-2xl space-y-4 overflow-hidden"
                >
                  <h4 className="text-[10px] font-black uppercase tracking-widest text-blue-400 flex items-center gap-1">
                    <Video className="w-3.5 h-3.5 text-red-500" /> Ajouter via YouTube (30 Bx)
                  </h4>
                  <div className="space-y-1">
                    <input
                      type="text"
                      placeholder="Nom de l'acteur"
                      aria-label="Nom de l'acteur"
                      value={quickName}
                      onChange={(e) => setQuickName(e.target.value)}
                      className="w-full bg-black/45 border border-white/5 rounded-lg px-3 py-2 text-xs font-bold text-white"
                    />
                  </div>
                  <div className="space-y-1">
                    <select
                      value={quickLang}
                      onChange={(e) => setQuickLang(e.target.value)}
                      className="w-full bg-black/45 border border-white/5 rounded-lg px-3 py-2 text-xs font-bold text-white"
                    >
                      <option value="japanese">Japonais (Seiyuu)</option>
                      <option value="french">Français (Doubleur)</option>
                    </select>
                  </div>
                  <div className="space-y-1">
                    <input
                      type="text"
                      placeholder="Lien YouTube ou recherche"
                      aria-label="Lien YouTube ou recherche"
                      value={quickSource}
                      onChange={(e) => setQuickSource(e.target.value)}
                      className="w-full bg-black/45 border border-white/5 rounded-lg px-3 py-2 text-xs font-bold text-white"
                    />
                  </div>
                  {quickError && (
                    <p className="text-[9px] font-bold text-red-400">⚠️ {quickError}</p>
                  )}
                  <div className="flex gap-2 justify-end">
                    <Button type="button" size="sm" variant="ghost" onClick={() => setShowQuickIngest(false)}>Annuler</Button>
                    <Button type="submit" size="sm" className="bg-blue-600 hover:bg-blue-500 border-none" disabled={isIngestingVoice}>
                      {isIngestingVoice ? <Loader2 className="w-3 h-3 animate-spin" /> : 'Ingérer'}
                    </Button>
                  </div>
                </motion.form>
              )}
            </AnimatePresence>

            {/* Language filter tab */}
            <div className="flex gap-1.5 p-1 bg-black/30 rounded-xl border border-white/5">
              {[
                { label: 'Tous', value: '' },
                { label: 'Seiyuu (JP)', value: 'japanese' },
                { label: 'VF (FR)', value: 'french' }
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setLangFilter(opt.value)}
                  className={`flex-1 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all ${
                    langFilter === opt.value
                      ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      : 'text-white/40 hover:text-white border border-transparent'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Seiyuu ou personnage..."
                aria-label="Rechercher un seiyuu ou un personnage"
                value={seiyuuQuery}
                onChange={(e) => {
                  setSeiyuuQuery(e.target.value);
                  searchSeiyuu(e.target.value, langFilter);
                }}
                className="w-full pl-12 pr-4 py-4 rounded-2xl bg-gray-50 dark:bg-gray-800 border-none outline-none focus:ring-2 focus:ring-blue-500 font-bold text-sm transition-all"
              />
              {isSearchingSeiyuu && <div className="absolute right-4 top-1/2 -translate-y-1/2 w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />}
            </div>
          </div>

          <div className="space-y-6 max-h-[800px] overflow-y-auto pr-2 custom-scrollbar">
            {seiyuuResults.map((s: VoiceProfile, idx: number) => (
              <div
                key={idx}
                draggable
                role="button"
                tabIndex={0}
                aria-label={`Sélectionner ou glisser le profil vocal ${s.name}`}
                onDragStart={(e) => onDragStart(e, s)}
                className="cursor-grab active:cursor-grabbing"
                onClick={() => selectVoiceProfile(s)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    selectVoiceProfile(s);
                  }
                }}
              >
                <Card padding="md" className={`group border-none relative overflow-hidden transition-all hover:ring-2 hover:ring-blue-500/50 ${selectedSeiyuu?.id === s.id ? 'ring-2 ring-blue-500' : ''}`}>
                  <div className="flex justify-between items-start mb-3">
                    <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                      <User className="w-4 h-4" />
                    </div>
                    <div className="flex gap-2">
                      <Badge variant="neutral" className="text-[7px] font-black uppercase tracking-tighter opacity-50 bg-black/40">
                        {s.language === 'japanese' ? '🇯🇵 JP' : s.language === 'french' ? '🇫🇷 FR' : '🌐'}
                      </Badge>
                      <Badge variant="neutral" className="text-[7px] font-black uppercase tracking-tighter opacity-40">
                        {s.origin === 'dataset' ? 'Dataset' : 'YouTube'}
                      </Badge>
                    </div>
                  </div>

                  <h4 className="text-lg font-black uppercase tracking-tight mb-0.5 flex items-center justify-between">
                    {s.name}
                    <button
                      onClick={(e) => playProfileSample(s.sample_url, e)}
                      className="p-1.5 rounded-lg bg-white/5 text-gray-400 hover:text-white hover:bg-blue-600 transition-colors"
                      title="Écouter l'échantillon"
                    >
                      <Volume2 className="w-3.5 h-3.5" />
                    </button>
                  </h4>
                  <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mb-4 leading-relaxed line-clamp-1">{s.roles || 'Doubleur'}</p>

                  <div className="space-y-3">
                    <div className="space-y-1">
                      <span className="text-[8px] font-black uppercase text-blue-500 tracking-widest flex items-center gap-1">
                        <Star className="w-2.5 h-2.5 fill-current" /> Rôles
                      </span>
                      <p className="text-[10px] font-medium leading-relaxed italic opacity-80 line-clamp-2">{s.roles || 'Aucun rôle répertorié'}</p>
                    </div>

                    <div className="pt-3 border-t border-black/5 dark:border-white/5 space-y-1">
                      <p className="text-[9px] leading-relaxed opacity-60 line-clamp-2">{s.definition || 'Talent vocal certifié.'}</p>
                    </div>
                  </div>

                  <div className="mt-4 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex-1 h-1 bg-blue-500/20 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-500 w-full animate-pulse" />
                    </div>
                    <span className="text-[7px] font-black uppercase text-blue-500">Cliquer ou Glisser pour utiliser</span>
                  </div>
                </Card>
              </div>
            ))}

            {seiyuuResults.length === 0 && !isSearchingSeiyuu && (
              <div className="py-20 text-center opacity-20">
                <Search className="w-8 h-8 mx-auto mb-4" />
                <p className="text-[10px] font-black uppercase tracking-widest">Aucun résultat</p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
};

export default AudioLabPage;
