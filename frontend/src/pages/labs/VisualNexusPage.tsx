import React, { useState } from 'react';
import { 
  Video, 
  Search, 
  Zap, 
  Sparkles, 
  Film, 
  Clock, 
  ChevronRight, 
  Play,
  Eye,
  Layers
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';

interface VideoSegment {
  video_id: string;
  start_time: number;
  end_time: number;
  description: string;
  score: number;
  thumbnail_url?: string;
  media_title?: string;
}

const VisualNexusPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState<VideoSegment[]>([]);

  const searchMutation = useMutation({
    mutationFn: (q: string) => apiClient(`/api/v1/labs/video/search/?q=${encodeURIComponent(q)}`),
    onSuccess: (data) => {
        setSearchResults(data.results || []);
    }
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
        searchMutation.mutate(query);
    }
  };

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Header Visual Nexus */}
        <header className="mb-16 text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-500 text-[10px] font-black uppercase tracking-[0.3em] mb-6">
               <Eye className="w-4 h-4 fill-current" /> SOTA Visual Understanding
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                VISUAL <span className="text-purple-500 text-glow">NEXUS</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-3xl mx-auto leading-relaxed">
                Trouvez des moments précis dans des milliers d'heures d'anime via l'indexation sémantique temporelle Video-LLaVA.
            </p>
        </header>

        {/* Search Bar Section */}
        <Card padding="lg" className="mb-16 bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 blur-3xl -mr-32 -mt-32" />
            
            <form onSubmit={handleSearch} className="relative z-10 space-y-8">
                <div className="flex gap-4">
                    <div className="relative flex-grow group">
                        <Search className="absolute left-6 top-1/2 -translate-y-1/2 w-6 h-6 text-white/20 group-focus-within:text-purple-500 transition-colors" />
                        <input
                            type="text"
                            aria-label="Décrire une scène à rechercher"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Décrivez une scène (ex: 'Un combat sous la pluie avec des éclairs bleus' ou 'Un personnage qui sourit tristement au coucher du soleil')..."
                            className="w-full bg-black border-2 border-white/5 rounded-[2.5rem] py-6 pl-16 pr-8 text-lg font-bold focus:border-purple-600 outline-none transition-all placeholder:opacity-20"
                        />
                    </div>
                    <Button 
                        type="submit" 
                        disabled={searchMutation.isPending || !query.trim()}
                        className="bg-purple-600 hover:bg-purple-500 text-white px-10 rounded-[2.5rem] font-black italic text-xl uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                    >
                        {searchMutation.isPending ? <Zap className="w-6 h-6 animate-spin" /> : "SCANNER LE MULTIVERS"}
                    </Button>
                </div>
                
                <div className="flex flex-wrap gap-4 px-6">
                    <span className="text-[10px] font-black uppercase tracking-widest opacity-20 py-2">Suggestions :</span>
                    {['Explosion nucléaire stylisée', 'Transformation magique rose', 'Repas de groupe chaleureux', 'Duel au sabre au clair de lune'].map(suggestion => (
                        <button 
                            key={suggestion}
                            type="button"
                            onClick={() => { setQuery(suggestion); searchMutation.mutate(suggestion); }}
                            className="text-[9px] font-black uppercase tracking-widest px-4 py-2 rounded-full bg-white/5 border border-white/5 hover:border-purple-500/30 hover:bg-purple-500/10 transition-all text-gray-400"
                        >
                            {suggestion}
                        </button>
                    ))}
                </div>
            </form>
        </Card>

        {/* Results Area */}
        <div className="space-y-12">
            <div className="flex items-center justify-between px-4">
                <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
                    <Layers className="w-4 h-4 text-purple-400" /> Segments Temporels Identifiés
                </h3>
                {searchResults.length > 0 && (
                    <Badge variant="primary" className="bg-purple-600 text-[8px] font-black">{searchResults.length} MOMENTS TROUVÉS</Badge>
                )}
            </div>

            <AnimatePresence mode="wait">
                {searchMutation.isPending ? (
                    <motion.div 
                        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
                    >
                        {[1, 2, 3].map(i => (
                            <Card key={i} className="aspect-video bg-white/5 border-white/5 animate-pulse rounded-3xl"><></></Card>
                        ))}
                    </motion.div>
                ) : searchResults.length > 0 ? (
                    <motion.div 
                        initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
                    >
                        {searchResults.map((segment, idx) => (
                            <motion.div 
                                key={idx}
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: idx * 0.1 }}
                            >
                                <Card padding="none" className="group overflow-hidden bg-navy-900/40 border-white/5 hover:border-purple-500/30 transition-all duration-500 rounded-3xl relative">
                                    <div className="aspect-video bg-black relative">
                                        {/* Mock Thumbnail or Placeholder */}
                                        <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-purple-900/20 to-black">
                                            <Film className="w-12 h-12 text-white/10 group-hover:scale-110 transition-transform duration-700" />
                                        </div>
                                        
                                        <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                            <div className="w-16 h-16 rounded-full bg-purple-600 flex items-center justify-center shadow-2xl scale-75 group-hover:scale-100 transition-transform duration-500">
                                                <Play className="w-8 h-8 text-white fill-current" />
                                            </div>
                                        </div>

                                        <div className="absolute bottom-4 right-4 px-3 py-1 bg-black/80 backdrop-blur-md rounded-lg text-[10px] font-mono font-bold text-white flex items-center gap-2">
                                            <Clock className="w-3 h-3 text-purple-400" />
                                            {Math.floor(segment.start_time / 60)}:{(segment.start_time % 60).toString().padStart(2, '0')} - {Math.floor(segment.end_time / 60)}:{(segment.end_time % 60).toString().padStart(2, '0')}
                                        </div>
                                        
                                        <Badge className="absolute top-4 left-4 bg-purple-600/80 border-none text-[8px] font-black uppercase">
                                            MATCH: {Math.round(segment.score * 100)}%
                                        </Badge>
                                    </div>

                                    <div className="p-6">
                                        <h4 className="font-black italic text-lg uppercase manga-font mb-2 truncate group-hover:text-purple-400 transition-colors">
                                            {segment.media_title || `Vidéo #${segment.video_id}`}
                                        </h4>
                                        <p className="text-[10px] font-bold opacity-40 uppercase leading-relaxed line-clamp-2 italic mb-4">
                                            "{segment.description}"
                                        </p>
                                        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-purple-500 opacity-0 group-hover:opacity-100 translate-x-[-10px] group-hover:translate-x-0 transition-all">
                                            Extraire ce segment <ChevronRight className="w-3 h-3" />
                                        </div>
                                    </div>
                                </Card>
                            </motion.div>
                        ))}
                    </motion.div>
                ) : (
                    <div className="text-center py-48 opacity-10 border-4 border-dashed border-white/5 rounded-[4rem]">
                        <Video className="w-32 h-32 mx-auto mb-8" />
                        <h3 className="text-4xl font-black italic manga-font uppercase mb-4">Moteur Optique Prêt</h3>
                        <p className="text-sm font-bold uppercase tracking-[0.3em]">Entrez une description pour scanner la base de clips.</p>
                    </div>
                )}
            </AnimatePresence>
        </div>

        {/* Guide & Protocole */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card padding="lg" className="bg-white dark:bg-black/40 border-purple-500/20 shadow-[0_0_50px_rgba(168,85,247,0.1)] relative overflow-hidden group">
                <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Eye className="w-64 h-64 text-purple-500" />
                </div>
                <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                    <Sparkles className="w-5 h-5 text-purple-600 dark:text-purple-400" /> Guide du Visual Nexus
                </h4>
                <div className="space-y-4 relative z-10">
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-purple-600 dark:text-purple-400">Le Concept :</span> Décrivez une scène avec vos mots ("un combat sous la pluie", "un sourire triste au coucher du soleil") et le moteur retrouve les passages correspondants dans la base de clips.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-purple-600 dark:text-purple-400">Les Résultats :</span> Chaque carte affiche le titre de la vidéo, le passage exact (minutage de début et de fin) et un score de correspondance avec votre description.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-purple-600 dark:text-purple-400">Les Suggestions :</span> Pas d'inspiration ? Cliquez sur une des suggestions sous la barre de recherche pour lancer un scan immédiat.
                    </p>
                </div>
            </Card>

            <div className="p-12 rounded-[4rem] bg-gradient-to-br from-purple-600/10 to-transparent border border-black/5 dark:border-white/5 flex flex-col justify-center text-center">
                <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-purple-800/70 dark:text-purple-200/60">
                    Les clips sont préalablement décrits par un modèle multimodal vidéo (Video-LLaVA) puis indexés sous forme de vecteurs sémantiques avec leurs bornes temporelles. <br />
                    Votre requête interroge cet index par similarité vectorielle et renvoie les segments les mieux notés, avec leur score de correspondance et leurs timecodes précis.
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default VisualNexusPage;


