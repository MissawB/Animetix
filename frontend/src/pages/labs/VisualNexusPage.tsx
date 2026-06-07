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
  Upload,
  Cpu,
  Eye,
  Layers
} from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { AnimatedPage } from '../../../components/ui/AnimatedPage';
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

        {/* Technical Infrastructure */}
        <div className="mt-32 p-12 rounded-[4rem] bg-navy-950 border border-white/5 grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="space-y-4">
                <div className="w-12 h-12 bg-purple-500/10 rounded-2xl flex items-center justify-center text-purple-500">
                    <Cpu className="w-6 h-6" />
                </div>
                <h4 className="font-black italic uppercase manga-font text-lg">Inférence Video-LLaVA</h4>
                <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Utilise des modèles multimodaux de pointe pour comprendre le mouvement, les couleurs et le contexte narratif des scènes.</p>
            </div>
            <div className="space-y-4">
                <div className="w-12 h-12 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-500">
                    <Clock className="w-6 h-6" />
                </div>
                <h4 className="font-black italic uppercase manga-font text-lg">Temporal Grounding</h4>
                <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Indexation précise au dixième de seconde près, permettant d'isoler des micro-événements dans des épisodes complets.</p>
            </div>
            <div className="space-y-4">
                <div className="w-12 h-12 bg-emerald-500/10 rounded-2xl flex items-center justify-center text-emerald-500">
                    <Sparkles className="w-6 h-6" />
                </div>
                <h4 className="font-black italic uppercase manga-font text-lg">CLIP-Video Latent</h4>
                <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Les clips sont projetés dans un espace latent vectoriel pour une recherche quasi-instantanée (Vector Search).</p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default VisualNexusPage;

