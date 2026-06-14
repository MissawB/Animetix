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
  Sparkles
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

interface SeiyuuResult {
  name: string;
  description: string;
  roles: string;
  impact: string;
  origin: string;
  sample_url: string;
}

interface SeiyuuApiResponse {
  query: string;
  results: SeiyuuResult[];
}

const SeiyuuDiscoveryPage: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeAudio, setActiveAudio] = useState<string | null>(null);

  const { data, isLoading, refetch, isRefetching } = useQuery<SeiyuuApiResponse>({
    queryKey: ['seiyuu-discovery', searchQuery],
    queryFn: () => apiClient(`/api/v1/labs/audio/seiyuu/?q=${encodeURIComponent(searchQuery)}`),
    enabled: false, // Don't run automatically
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
    setActiveAudio(url);
    const audio = new Audio(url);
    audio.play().catch(err => {
        console.error("Audio playback failed:", err);
        setActiveAudio(null);
    });
    audio.onended = () => setActiveAudio(null);
  };

  return (
    <div className="min-h-screen w-full bg-[#0a0a0f] text-white pt-20 pb-32">
      <AnimatedPage>
        <div className="max-w-7xl mx-auto px-6 relative z-10">
          
          {/* Header Section */}
          <header className="mb-20 relative">
              <div className="absolute -top-24 -left-24 w-96 h-96 bg-emerald-500/10 blur-[120px] rounded-full -z-10" />
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-emerald-400 mb-6">
                  <Mic2 className="w-3 h-3" /> Voice Actor Intelligent Discovery
              </div>
              <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4 leading-none">
                  SEIYUU <span className="text-emerald-500 text-glow">DISCOVERY</span>
              </h1>
              <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                  Identifiez les voix iconiques de l'animation japonaise et analysez leur profil vocal.
              </p>
          </header>

          {/* Search Bar */}
          <div className="mb-20">
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
              <div className="flex gap-4 mt-6 px-4">
                  {['Rie Takahashi', 'Hiroshi Kamiya', 'Mamoru Miyano', 'Mikasa', 'Eren Yeager'].map(tag => (
                      <button 
                          key={tag}
                          onClick={() => { setSearchQuery(tag); setTimeout(() => refetch(), 10); }}
                          className="text-[10px] font-black uppercase tracking-widest text-white/30 hover:text-emerald-400 transition-colors"
                      >
                          # {tag}
                      </button>
                  ))}
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
                                  transition={{ delay: i * 0.1 }}
                              >
                                  <Card padding="none" className="bg-navy-950/40 border-white/5 hover:border-emerald-500/30 transition-all duration-500 overflow-hidden relative group">
                                      <div className="p-10 flex flex-col md:flex-row gap-10">
                                          {/* Avatar Placeholder / Visual */}
                                          <div className="w-32 h-32 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform overflow-hidden relative">
                                              <Users className="w-12 h-12 text-white/10" />
                                              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                                          </div>

                                          <div className="flex-grow space-y-6">
                                              <header className="flex justify-between items-start">
                                                  <div>
                                                      <h3 className="text-3xl font-black italic manga-font uppercase text-white mb-1 group-hover:text-emerald-400 transition-colors">
                                                          {seiyuu.name}
                                                      </h3>
                                                      <Badge variant="neutral" className="bg-emerald-500/10 text-emerald-400 border-none text-[8px] italic font-black uppercase tracking-widest">
                                                          {seiyuu.origin}
                                                      </Badge>
                                                  </div>
                                                  <button 
                                                      onClick={() => playSample(seiyuu.sample_url)}
                                                      className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all ${
                                                          activeAudio === seiyuu.sample_url 
                                                          ? 'bg-emerald-500 text-white animate-pulse' 
                                                          : 'bg-white/5 text-white hover:bg-emerald-600'
                                                      }`}
                                                  >
                                                      {activeAudio === seiyuu.sample_url ? <Volume2 className="w-6 h-6" /> : <Play className="w-6 h-6 ml-1" />}
                                                  </button>
                                              </header>

                                              <p className="text-sm font-medium text-white/40 leading-relaxed italic">
                                                  "{seiyuu.description}"
                                              </p>

                                              <div className="space-y-4">
                                                  <h4 className="text-[10px] font-black uppercase tracking-widest text-white/20 flex items-center gap-2">
                                                      <Star className="w-3 h-3" /> Iconic Roles
                                                  </h4>
                                                  <div className="flex flex-wrap gap-2">
                                                      {seiyuu.roles.split(',').map((role, idx) => (
                                                          <Badge key={idx} variant="outline" className="border-white/10 text-white/60 bg-white/5 px-3 py-1 rounded-lg text-[9px] font-bold uppercase">
                                                              {role.trim()}
                                                          </Badge>
                                                      ))}
                                                  </div>
                                              </div>

                                              <div className="pt-6 border-t border-white/5 flex items-center justify-between">
                                                  <div className="flex items-center gap-2">
                                                      <Sparkles className="w-3 h-3 text-emerald-500" />
                                                      <span className="text-[9px] font-black uppercase text-emerald-500/50">Impact Score: {seiyuu.impact}</span>
                                                  </div>
                                                  <Button variant="ghost" className="p-0 text-[9px] font-black uppercase tracking-widest text-white/30 hover:text-white transition-colors group">
                                                      Voice Analysis <ChevronRight className="w-3 h-3 inline group-hover:translate-x-1 transition-transform" />
                                                  </Button>
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
                          <p className="text-sm font-bold uppercase tracking-[0.4em] text-white/10">Essayez une autre fréquence vocale.</p>
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
