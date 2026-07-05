import React, { useState } from 'react';
import {
  Mic,
  Play,
  Save,
  User,
  MessageSquare,
  Wand2,
  Search,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { apiClient } from "../../utils/apiClient";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';
import { VoiceProfile } from '../../types';
import { useToastStore } from '../../store/toastStore';

const MangaVoicePage: React.FC = () => {
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
  const { data: profilesData, isLoading: isLoadingProfiles } = useQuery<{ results: VoiceProfile[] }>({
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
      setCharacter(file.name.replace(/\.[^/.]+$/, ""));
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
      console.error("Failed to load reference audio from profile:", err);
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
        headers: {}
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
    <AnimatedPage>
      <div className="container mx-auto py-12 px-6">
        <header className="mb-16 text-center md:text-left">
          <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase mb-4">
            MANGA <span className="text-orange-500 text-glow">VOICE</span> LAB
          </h1>
          <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
            Donnez vie à vos planches avec le doublage IA zero-shot et le clonage vocal instantané.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Casting Panel (Left) */}
          <Card padding="lg" className="lg:col-span-4 h-fit bg-gray-900/40 border-white/5 shadow-2xl space-y-6">
            <div>
              <h3 className="text-xs font-black uppercase opacity-40 mb-4 tracking-widest flex items-center gap-2">
                <User className="w-4 h-4" /> Casting Vocal
              </h3>
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                Choisissez une voix de la BDD ou chargez votre propre extrait.
              </p>
            </div>

            {/* Language filter tab */}
            <div className="flex gap-1 bg-black/40 p-1 rounded-xl border border-white/5">
              {[
                { label: 'Tous', value: '' },
                { label: 'Seiyuu (JP)', value: 'japanese' },
                { label: 'VF (FR)', value: 'french' }
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setLangFilter(opt.value)}
                  className={`flex-1 py-2 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all ${
                    langFilter === opt.value
                      ? 'bg-orange-500/10 text-orange-400 border border-orange-500/20'
                      : 'text-white/40 hover:text-white border border-transparent'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            {/* Quick Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Rechercher une voix..."
                aria-label="Rechercher une voix"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-black/40 border border-white/5 rounded-xl pl-10 pr-4 py-3 font-bold text-xs outline-none focus:border-orange-500/50"
              />
            </div>

            {/* Profiles List */}
            <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1 custom-scrollbar">
              {isLoadingProfiles ? (
                <div className="py-10 text-center">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto text-orange-500" />
                </div>
              ) : profilesData?.results && profilesData.results.length > 0 ? (
                profilesData.results.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => handleSelectProfile(p)}
                    className={`w-full px-4 py-3.5 rounded-xl text-left text-xs font-black transition-all border flex items-center justify-between group ${
                      selectedProfile?.id === p.id
                        ? 'border-orange-500 bg-orange-500/10 text-white shadow-lg'
                        : 'border-white/5 bg-black/25 text-white/50 hover:border-white/10 hover:text-white'
                    }`}
                  >
                    <div className="flex flex-col gap-0.5 truncate pr-2">
                      <span className="truncate">{p.name}</span>
                      <span className="text-[8px] opacity-40 truncate font-medium uppercase tracking-wide">
                        {p.roles || 'Doubleur'}
                      </span>
                    </div>
                    <Badge variant="neutral" className="text-[7px] font-black uppercase shrink-0 bg-black/40">
                      {p.language === 'japanese' ? '🇯🇵 JP' : p.language === 'french' ? '🇫🇷 FR' : '🌐'}
                    </Badge>
                  </button>
                ))
              ) : (
                <div className="py-10 text-center text-white/20">
                  <span className="text-[10px] font-black uppercase">Aucune voix trouvée</span>
                </div>
              )}
            </div>

            <div className="pt-6 border-t border-white/5 space-y-4">
              <div>
                <h4 className="text-[10px] font-black uppercase opacity-30 tracking-widest">Ou charger manuellement</h4>
              </div>
              <Button
                variant="outline"
                fullWidth
                className="bg-black text-white hover:bg-gray-800 border-none rounded-xl py-4 flex items-center justify-center gap-2"
                onClick={() => document.getElementById('audio-upload')?.click()}
              >
                <Mic className="w-4 h-4" /> {refAudio && !selectedProfile ? 'VOIX MANUELLE CHARGÉE' : 'CHARGER UN WAV/MP3'}
              </Button>
              <input type="file" id="audio-upload" className="hidden" accept="audio/*" onChange={handleFileChange} aria-label="Charger un fichier audio de référence" />
              {refAudio && (
                <div className="p-3 bg-white/5 rounded-xl flex items-center justify-between text-xs font-bold">
                  <span className="truncate max-w-[200px] opacity-60">{refAudio.name}</span>
                  {loadingAudio ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-orange-500" />
                  ) : (
                    <Badge variant="success" className="text-[8px] bg-orange-500">PRÊT</Badge>
                  )}
                </div>
              )}
            </div>
          </Card>

          {/* Dialog and Result Area (Right) */}
          <div className="lg:col-span-8 space-y-8">
            <Card padding="lg" className="bg-black border-2 border-white/5 rounded-[3rem] shadow-2xl">
              <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-orange-500" /> Script du Dialogue
              </h3>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                aria-label="Script du dialogue"
                placeholder={refAudio ? `Entrez le texte que ${character} doit dire...` : "Sélectionnez d'abord un doubleur dans le menu de gauche..."}
                disabled={!refAudio}
                className="w-full h-40 bg-gray-900/50 border border-white/5 rounded-2xl p-6 text-lg font-bold text-white outline-none focus:border-orange-500/50 transition-all resize-none placeholder:opacity-20"
              />
              <div className="flex justify-end mt-6">
                <Button
                  onClick={handleGenerate}
                  disabled={!text || !refAudio || loading || loadingAudio}
                  className="bg-orange-500 hover:bg-orange-400 text-white px-12 py-8 rounded-2xl font-black italic text-xl uppercase shadow-xl shadow-orange-500/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
                >
                  {loading ? <Wand2 className="w-6 h-6 animate-spin" /> : "GÉNÉRER LE DUBBING"}
                </Button>
              </div>
            </Card>

            <AnimatePresence>
              {audioUrl && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                >
                  <Card padding="lg" className="bg-gradient-to-br from-orange-500/20 to-transparent border-orange-500/30 rounded-[3rem] p-10 flex flex-col items-center gap-8 shadow-2xl relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-6">
                      <Badge variant="success" className="bg-orange-500 text-white font-black italic border-none px-4 py-2">RVC v2 OPTIMIZED</Badge>
                    </div>

                    <div className="w-24 h-24 bg-orange-500 rounded-full flex items-center justify-center shadow-2xl shadow-orange-500/50 animate-pulse cursor-pointer">
                      <Play className="w-10 h-10 text-white ml-1" />
                    </div>

                    <div className="text-center">
                      <h3 className="text-2xl font-black italic manga-font uppercase mb-2 tracking-tighter">Dubbing Terminé</h3>
                      <p className="text-xs font-bold opacity-50 uppercase tracking-widest">Le personnage de {character} est prêt à parler.</p>
                    </div>

                    <audio controls src={audioUrl} className="w-full max-w-xl accent-orange-500" aria-label="Lecteur audio du doublage généré">
                      <track kind="captions" />
                    </audio>

                    <div className="flex gap-4">
                      <Button variant="outline" className="border-white/10 hover:bg-white/5 rounded-xl px-8">
                        <Save className="w-4 h-4 mr-2" /> SAUVEGARDER
                      </Button>
                      <Button variant="primary" className="bg-white text-black hover:bg-gray-200 border-none rounded-xl px-8 font-black uppercase italic">
                        INJECTER DANS LA PLANCHE
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>

            {!audioUrl && !loading && (
              <div className="h-64 border-4 border-dashed border-white/5 rounded-[3rem] flex flex-col items-center justify-center opacity-20">
                <Mic className="w-16 h-16 mb-4" />
                <span className="font-black italic uppercase tracking-widest">En attente de génération</span>
              </div>
            )}
          </div>
        </div>

        {/* Guide & Protocole */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card padding="lg" className="bg-white dark:bg-black/40 border-orange-500/20 shadow-[0_0_50px_rgba(249,115,22,0.1)] relative overflow-hidden group">
                <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Mic className="w-64 h-64 text-orange-500" />
                </div>
                <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                    <Sparkles className="w-5 h-5 text-orange-600 dark:text-orange-400" /> Guide du Dubbing
                </h4>
                <div className="space-y-4 relative z-10">
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-orange-600 dark:text-orange-400">Le Casting :</span> Choisissez un doubleur dans le catalogue (filtrable par langue JP/FR) ou chargez votre propre extrait WAV/MP3 comme voix de référence.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-orange-600 dark:text-orange-400">Le Script :</span> Écrivez la réplique que le personnage doit dire, puis lancez la génération : la voix choisie prononce votre texte.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-orange-600 dark:text-orange-400">Le Résultat :</span> Écoutez le doublage dans le lecteur intégré : idéal pour donner de la voix à une planche de manga ou tester un casting.
                    </p>
                </div>
            </Card>

            <div className="p-12 rounded-[4rem] bg-gradient-to-br from-orange-600/10 to-transparent border border-black/5 dark:border-white/5 flex flex-col justify-center text-center">
                <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-orange-800/70 dark:text-orange-200/60">
                    Clonage vocal zero-shot : le texte et un échantillon audio de référence sont envoyés à l'endpoint manga-voice, qui conditionne la synthèse vocale sur ce timbre sans entraînement préalable. <br />
                    Les profils du catalogue fournissent l'échantillon automatiquement ; la sortie est affinée via conversion RVC v2.
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default MangaVoicePage;
