import React, { useState } from 'react';
import {
  Mic2,
  Search,
  Play,
  Volume2,
  Users,
  Star,
  Info,
  Loader2,
  Music,
  ChevronRight,
  Sparkles,
  Plus,
  Video,
  Globe,
  Database,
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';
import type { IngestVoicePayload } from '../../features/labs/services/audioLabService';

interface SeiyuuResult {
  id: number;
  name: string;
  language: 'japanese' | 'french' | 'other';
  origin: 'dataset' | 'youtube' | 'upload';
  definition?: string;
  roles?: string;
  impact?: string;
  origin_detail?: string;
  sample_url: string;
}

interface SeiyuuApiResponse {
  query: string;
  results: SeiyuuResult[];
}

const SeiyuuDiscoveryPage: React.FC = () => {
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
    enabled: true, // Run on load to show indexed profiles
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
    audio.play()
      .then(() => {
        setAudioLoading(null);
        setActiveAudio(url);
      })
      .catch(err => {
        console.error("Audio playback failed:", err);
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
      setIngestSuccess(`La voix de '${response.profile.name}' a été ingérée et nettoyée avec succès !`);
      setIngestName('');
      setIngestSource('');
      setIngestDef('');
      setIngestRoles('');
      // Trigger search for the newly ingesting actor
      setSearchQuery(response.profile.name);
      setTimeout(() => {
        refetch();
        setShowIngestForm(false);
        setIngestSuccess('');
      }, 3000);
    },
    onError: (err: unknown) => {
      const message = err instanceof Error ? err.message : '';
      setIngestError(message || "Une erreur est survenue lors du téléchargement ou du traitement audio.");
    }
  });

  const handleIngestSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIngestError('');
    setIngestSuccess('');

    if (!ingestName || !ingestSource) {
      setIngestError("Le nom et l'URL/requête YouTube sont obligatoires.");
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
                Explorez les voix cultes (Seiyuus & Doubleurs) et ingérez de nouvelles voix à la volée.
              </p>
            </div>
            <div>
              <Button
                onClick={() => setShowIngestForm(!showIngestForm)}
                className="bg-emerald-600 hover:bg-emerald-500 border-none text-white font-black italic uppercase px-8 py-4 rounded-2xl flex items-center gap-2 shadow-lg hover:shadow-emerald-500/20 hover:scale-105 transition-all"
              >
                {showIngestForm ? 'Fermer le panel' : <><Plus className="w-5 h-5" /> Ingestion YouTube</>}
              </Button>
            </div>
          </header>

          {/* Ingestion Panel */}
          <AnimatePresence>
            {showIngestForm && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden mb-12"
              >
                <Card padding="lg" className="bg-[#12121e]/80 border border-emerald-500/20 backdrop-blur-xl rounded-[2.5rem] p-8">
                  <h3 className="text-2xl font-black italic uppercase manga-font flex items-center gap-3 mb-6 text-emerald-400">
                    <Video className="w-6 h-6 text-red-500" /> Ingestion et extraction vocale
                  </h3>
                  <p className="text-xs font-bold opacity-50 uppercase tracking-widest mb-6">
                    Coût : <span className="text-emerald-400">30 Bx</span> — L'IA télécharge l'audio, isole les fréquences vocales (80Hz - 8000Hz) et découpe un échantillon de 10s sans silence.
                  </p>

                  <form onSubmit={handleIngestSubmit} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label htmlFor="ingest-name" className="text-[10px] font-black uppercase tracking-wider opacity-60">Nom du Doubleur / Seiyuu</label>
                        <input
                          id="ingest-name"
                          type="text"
                          value={ingestName}
                          onChange={(e) => setIngestName(e.target.value)}
                          placeholder="Ex: Donald Reignoux, Rie Takahashi"
                          className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50"
                        />
                      </div>
                      <div className="space-y-2">
                        <label htmlFor="ingest-lang" className="text-[10px] font-black uppercase tracking-wider opacity-60">Langue / Spécialisation</label>
                        <select
                          id="ingest-lang"
                          value={ingestLang}
                          onChange={(e) => setIngestLang(e.target.value)}
                          className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50 text-white"
                        >
                          <option value="japanese">Japonais (Seiyuu)</option>
                          <option value="french">Français (Doubleur)</option>
                          <option value="other">Autre</option>
                        </select>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label htmlFor="ingest-source" className="text-[10px] font-black uppercase tracking-wider opacity-60">URL YouTube ou requête de recherche</label>
                      <input
                        id="ingest-source"
                        type="text"
                        value={ingestSource}
                        onChange={(e) => setIngestSource(e.target.value)}
                        placeholder="Ex: https://www.youtube.com/watch?v=... ou 'Donald Reignoux Titeuf interview'"
                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="space-y-2">
                        <label htmlFor="ingest-def" className="text-[10px] font-black uppercase tracking-wider opacity-60">Définition / Description (optionnel)</label>
                        <textarea
                          id="ingest-def"
                          value={ingestDef}
                          onChange={(e) => setIngestDef(e.target.value)}
                          placeholder="Ex: Acteur français à voix claire, connu pour doubler Sora..."
                          className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50 h-24 resize-none"
                        />
                      </div>
                      <div className="space-y-2">
                        <label htmlFor="ingest-roles" className="text-[10px] font-black uppercase tracking-wider opacity-60">Iconic Roles (séparés par des virgules)</label>
                        <textarea
                          id="ingest-roles"
                          value={ingestRoles}
                          onChange={(e) => setIngestRoles(e.target.value)}
                          placeholder="Ex: Sora, Spider-Man, Titeuf, Reese"
                          className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50 h-24 resize-none"
                        />
                      </div>
                    </div>

                    {ingestError && (
                      <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 font-bold rounded-xl text-xs">
                        ⚠️ {ingestError}
                      </div>
                    )}

                    {ingestSuccess && (
                      <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-black rounded-xl text-xs flex items-center gap-2 animate-pulse">
                        <Sparkles className="w-4 h-4 text-glow" /> {ingestSuccess}
                      </div>
                    )}

                    <div className="flex justify-end gap-4 pt-2">
                      <Button
                        type="button"
                        variant="ghost"
                        onClick={() => setShowIngestForm(false)}
                      >
                        Annuler
                      </Button>
                      <Button
                        type="submit"
                        disabled={ingestMutation.isPending}
                        className="bg-emerald-600 hover:bg-emerald-500 text-white font-black italic uppercase px-8 py-3 rounded-xl flex items-center gap-2 border-none"
                      >
                        {ingestMutation.isPending ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" /> Ingestion en cours...
                          </>
                        ) : (
                          'Lancer l\'ingestion'
                        )}
                      </Button>
                    </div>
                  </form>
                </Card>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Search Bar & Filters */}
          <div className="mb-12 space-y-6">
            <form onSubmit={handleSearch} className="relative group">
              <div className="absolute inset-0 bg-emerald-500/20 blur-3xl opacity-0 group-focus-within:opacity-100 transition-opacity -z-10" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Chercher par nom de doubleur ou nom de personnage..."
                className="w-full bg-black/40 backdrop-blur-xl border-2 border-white/5 focus:border-emerald-500/50 rounded-[2.5rem] px-10 py-8 text-xl font-bold outline-none transition-all text-white placeholder:text-white/10"
              />
              <div className="absolute right-4 top-1/2 -translate-y-1/2 flex gap-4">
                <Button
                  type="submit"
                  disabled={isLoading || isRefetching}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-10 py-5 rounded-2xl font-black italic uppercase shadow-xl transition-all border-none flex items-center gap-3"
                >
                  {isLoading || isRefetching ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Search className="w-5 h-5" /> RECHERCHER</>}
                </Button>
              </div>
            </form>

            {/* Quick Filters */}
            <div className="flex flex-wrap items-center justify-between gap-6 px-4">
              <div className="flex flex-wrap gap-4 items-center">
                <span className="text-[9px] font-black uppercase tracking-widest text-white/30 flex items-center gap-1">
                  <Globe className="w-3 h-3" /> Langue:
                </span>
                <div className="flex gap-2">
                  {[
                    { label: 'Tous', value: '' },
                    { label: 'Japonais (Seiyuu)', value: 'japanese' },
                    { label: 'Français (Doubleur)', value: 'french' },
                  ].map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => setLangFilter(opt.value)}
                      className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all border ${
                        langFilter === opt.value
                          ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400'
                          : 'bg-white/5 border-white/5 text-white/60 hover:border-white/10 hover:text-white'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex flex-wrap gap-4 items-center">
                <span className="text-[9px] font-black uppercase tracking-widest text-white/30 flex items-center gap-1">
                  <Database className="w-3 h-3" /> Origine:
                </span>
                <div className="flex gap-2">
                  {[
                    { label: 'Tous', value: '' },
                    { label: 'Dataset HF', value: 'dataset' },
                    { label: 'YouTube Ingest', value: 'youtube' },
                  ].map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => setOriginFilter(opt.value)}
                      className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all border ${
                        originFilter === opt.value
                          ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400'
                          : 'bg-white/5 border-white/5 text-white/60 hover:border-white/10 hover:text-white'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

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
                    <motion.div
                      key={seiyuu.name}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                    >
                      <Card padding="none" className="bg-navy-950/40 border-white/5 hover:border-emerald-500/30 transition-all duration-500 overflow-hidden relative group">
                        <div className="p-10 flex flex-col md:flex-row gap-10">
                          {/* Visual Indicator */}
                          <div className="w-32 h-32 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform overflow-hidden relative">
                            <Users className="w-12 h-12 text-white/10" />
                            <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                            <span className="absolute bottom-2 right-2 text-[8px] font-black px-2 py-0.5 bg-black/60 rounded border border-white/10 uppercase">
                              {seiyuu.language === 'japanese' ? '🇯🇵 JP' : seiyuu.language === 'french' ? '🇫🇷 FR' : '🌐'}
                            </span>
                          </div>

                          <div className="flex-grow space-y-6">
                            <header className="flex justify-between items-start">
                              <div>
                                <h3 className="text-3xl font-black italic manga-font uppercase text-white mb-1 group-hover:text-emerald-400 transition-colors">
                                  {seiyuu.name}
                                </h3>
                                <div className="flex gap-2 items-center">
                                  <Badge variant="neutral" className="bg-emerald-500/10 text-emerald-400 border-none text-[8px] italic font-black uppercase tracking-widest">
                                    {seiyuu.origin === 'dataset' ? 'Dataset Hugging Face' : seiyuu.origin === 'youtube' ? 'Ingestion YouTube' : 'Manuel'}
                                  </Badge>
                                </div>
                              </div>
                              <button
                                onClick={() => playSample(seiyuu.sample_url)}
                                disabled={audioLoading === seiyuu.sample_url}
                                className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all ${
                                  activeAudio === seiyuu.sample_url
                                    ? 'bg-emerald-500 text-white animate-pulse'
                                    : 'bg-white/5 text-white hover:bg-emerald-600'
                                }`}
                              >
                                {audioLoading === seiyuu.sample_url ? (
                                  <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
                                ) : activeAudio === seiyuu.sample_url ? (
                                  <Volume2 className="w-6 h-6" />
                                ) : (
                                  <Play className="w-6 h-6 ml-1" />
                                )}
                              </button>
                            </header>

                            <p className="text-sm font-medium text-white/40 leading-relaxed italic">
                              "{seiyuu.definition || 'Pas de description supplémentaire pour cette voix.'}"
                            </p>

                            {seiyuu.roles && (
                              <div className="space-y-4">
                                <h4 className="text-[10px] font-black uppercase tracking-widest text-white/20 flex items-center gap-2">
                                  <Star className="w-3 h-3" /> Iconic Roles
                                </h4>
                                <div className="flex flex-wrap gap-2">
                                  {seiyuu.roles.split(',').map((role, idx) => (
                                    <Badge key={idx} variant="neutral" className="border-white/10 text-white/60 bg-white/5 px-3 py-1 rounded-lg text-[9px] font-bold uppercase">
                                      {role.trim()}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}

                            <div className="pt-6 border-t border-white/5 flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <Sparkles className="w-3 h-3 text-emerald-500" />
                                <span className="text-[9px] font-black uppercase text-emerald-500/50">Impact Score: {seiyuu.impact || 'Custom'}</span>
                              </div>
                              {seiyuu.origin_detail && seiyuu.origin_detail.startsWith('http') && (
                                <a
                                  href={seiyuu.origin_detail}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-[9px] font-black uppercase tracking-widest text-white/30 hover:text-emerald-400 transition-colors flex items-center gap-1"
                                >
                                  Source Originale <ChevronRight className="w-3 h-3" />
                                </a>
                              )}
                            </div>
                          </div>
                        </div>
                      </Card>
                    </motion.div>
                  ))}
                </motion.div>
              ) : data && searchQuery ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="py-32 text-center border-4 border-dashed border-white/5 rounded-[4rem]"
                >
                  <Info className="w-20 h-24 mx-auto mb-8 text-white/10" />
                  <h3 className="text-4xl font-black italic uppercase manga-font text-white/20">Aucun profil trouvé</h3>
                  <p className="text-sm font-bold uppercase tracking-[0.4em] text-white/10">Essayez de lancer une ingestion depuis YouTube !</p>
                </motion.div>
              ) : !isLoading && !isRefetching && (
                <div className="py-32 text-center opacity-10 flex flex-col items-center border-4 border-dashed border-white/5 rounded-[4rem]">
                  <Music className="w-32 h-32 mb-12" />
                  <h3 className="text-5xl font-black italic uppercase manga-font mb-4">Neural Vocal Base</h3>
                  <p className="text-lg font-bold uppercase tracking-[0.4em]">Prêt pour l'indexation sémantique des fréquences.</p>
                </div>
              )}
            </AnimatePresence>
          </div>

          {/* Technology Guide */}
          <div className="mt-32 grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card padding="lg" className="bg-black/40 border-white/5">
              <h4 className="text-xs font-black uppercase tracking-widest text-emerald-400 mb-4">Vocal Fingerprinting</h4>
              <p className="text-[10px] font-bold text-white/40 uppercase leading-relaxed">
                L'IA analyse les harmoniques et le timbre unique pour catégoriser les voix selon 12 dimensions psycho-acoustiques.
              </p>
            </Card>
            <Card padding="lg" className="bg-black/40 border-white/5">
              <h4 className="text-xs font-black uppercase tracking-widest text-emerald-400 mb-4">Cross-Lore Index</h4>
              <p className="text-[10px] font-bold text-white/40 uppercase leading-relaxed">
                Recherche croisée permettant de découvrir les liens cachés entre différents studios via la réutilisation des talents vocaux.
              </p>
            </Card>
            <Card padding="lg" className="bg-black/40 border-white/5">
              <h4 className="text-xs font-black uppercase tracking-widest text-emerald-400 mb-4">Audio SOTA Samples</h4>
              <p className="text-[10px] font-bold text-white/40 uppercase leading-relaxed">
                Chaque profil inclut un échantillon audio haute fidélité pour une vérification instantanée de la signature vocale.
              </p>
            </Card>
          </div>

        </div>
      </AnimatedPage>
    </div>
  );
};

export default SeiyuuDiscoveryPage;
