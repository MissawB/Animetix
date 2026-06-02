import React, { useState } from 'react';
import { 
  Globe,
  Loader2,
  ChevronRight,
  ShieldCheck,
  Zap,
  Target,
  Layers,
  Users,
  Film,
  Sparkles
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';

const MultiverseLabPage: React.FC = () => {
  const [universeName, setUniverseName] = useState('ShinSekai');
  const [genre, setGenre] = useState('Cyberpunk');
  const [synthesizedResult, setSynthesizedResult] = useState<any | null>(null);

  const synthesizeMutation = useMutation({
    mutationFn: (body: any) => apiClient('/api/v1/singularity-lab/', { 
        method: 'POST', 
        body: JSON.stringify(body) 
    }),
    onSuccess: (data) => setSynthesizedResult(data)
  });

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Header */}
        <header className="mb-16 relative">
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-red-500/10 blur-[120px] rounded-full -z-10" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-red-400 mb-4">
                <Globe className="w-3 h-3" /> Autonomous Domain Synthesizer
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                MULTIVERSE <span className="text-red-600 text-glow">GENERATOR</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Génération autonome de segments narratifs et de cohérence de monde (ADMS).
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            
            {/* Configuration */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl overflow-hidden relative">
                    <div className="absolute top-0 right-0 p-6 opacity-10">
                        <Globe className="w-24 h-24 rotate-12" />
                    </div>
                    
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-red-500" /> Genesis Config
                    </h3>

                    <div className="space-y-8">
                        <div className="space-y-6">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black opacity-30 uppercase tracking-widest px-2">Nom de l'Univers</label>
                                <input 
                                    type="text" 
                                    value={universeName} 
                                    onChange={(e) => setUniverseName(e.target.value)} 
                                    className="w-full bg-black border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold focus:border-red-500 outline-none transition-all" 
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black opacity-30 uppercase tracking-widest px-2">Genre Dominant</label>
                                <select 
                                    value={genre} 
                                    onChange={(e) => setGenre(e.target.value)} 
                                    className="w-full bg-black border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold text-white outline-none focus:border-red-500 transition-all"
                                >
                                    <option value="Cyberpunk">Cyberpunk</option>
                                    <option value="Sci-Fi">Sci-Fi</option>
                                    <option value="Fantasy">Fantasy</option>
                                    <option value="Steampunk">Steampunk</option>
                                    <option value="Isekai">Isekai</option>
                                </select>
                            </div>
                        </div>

                        <Button 
                            onClick={() => synthesizeMutation.mutate({ action: 'synthesize', universe_name: universeName, genre: genre })} 
                            disabled={synthesizeMutation.isPending} 
                            className="w-full bg-red-600 hover:bg-red-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                        >
                            {synthesizeMutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "GÉNÉRER LE MONDE"}
                        </Button>
                    </div>
                </Card>

                <Card padding="lg" className="bg-white/5 border-white/5 opacity-50">
                    <h4 className="text-[10px] font-black uppercase tracking-widest mb-4 text-red-400">Algorithme ADMS</h4>
                    <p className="text-[10px] font-bold uppercase leading-relaxed mb-4">
                        L'Autonomous Domain Synthesizer crée des structures de lore auto-cohérentes prêtes pour Neo4j.
                    </p>
                    <ul className="space-y-3">
                        <li className="flex gap-2 text-[8px] font-black opacity-40 uppercase">
                            <div className="w-1 h-1 rounded-full bg-red-500 mt-1" /> Cohérence diégétique IA.
                        </li>
                        <li className="flex gap-2 text-[8px] font-black opacity-40 uppercase">
                            <div className="w-1 h-1 rounded-full bg-red-500 mt-1" /> Export sémantique vers Graphes.
                        </li>
                    </ul>
                </Card>
            </div>

            {/* Results Grid */}
            <div className="lg:col-span-8">
                <AnimatePresence mode="wait">
                    {synthesizedResult ? (
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                {[
                                    { label: 'Cohérence (IA)', val: synthesizedResult.evaluation.ai_score, threshold: 0.7 },
                                    { label: 'Immersion Score', val: synthesizedResult.evaluation.community_score, threshold: 0.7 }
                                ].map(s => (
                                    <Card key={s.label} padding="lg" className="bg-navy-950 border-white/5 flex flex-col justify-between h-36 shadow-xl">
                                        <span className="text-[10px] font-black uppercase opacity-40 tracking-widest">{s.label}</span>
                                        <div className="flex items-end justify-between">
                                            <span className={`text-6xl font-black italic manga-font ${s.val >= s.threshold ? 'text-emerald-400' : 'text-red-400'}`}>
                                                {Math.round(s.val * 100)}%
                                            </span>
                                            <div className="w-12 h-1 bg-white/5 rounded-full overflow-hidden mb-2">
                                                <div className="h-full bg-current" style={{ width: `${s.val * 100}%` }} />
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                                <Card padding="lg" className="bg-navy-950 border-white/5 flex flex-col justify-between h-36 shadow-xl relative overflow-hidden">
                                    <div className="absolute -right-4 -bottom-4 opacity-5">
                                        <Zap className="w-24 h-24" />
                                    </div>
                                    <span className="text-[10px] font-black uppercase opacity-40 tracking-widest">Statut Neo4j</span>
                                    <div className={`text-2xl font-black italic uppercase manga-font ${synthesizedResult.persisted ? 'text-blue-400' : 'text-orange-400'}`}>
                                        {synthesizedResult.persisted ? 'PERSISTÉ' : 'TEMP_CACHE'}
                                    </div>
                                    <Badge variant="neutral" className="w-fit bg-white/5 border-none text-[8px] font-black italic">INTEGRITY_CHECK: PASS</Badge>
                                </Card>
                            </div>

                            <div className="bg-black/60 backdrop-blur-xl p-16 rounded-[4rem] border-2 border-white/5 space-y-12 relative overflow-hidden shadow-2xl">
                                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-red-600/5 blur-[120px] -mr-64 -mt-64" />
                                
                                <header className="flex justify-between items-center border-b border-white/10 pb-10">
                                    <div className="space-y-2">
                                        <h2 className="text-6xl font-black italic text-red-500 manga-font uppercase tracking-tighter leading-none">
                                            {synthesizedResult.universe.name}
                                        </h2>
                                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-[0.5em]">Sector: {synthesizedResult.universe.genre}</p>
                                    </div>
                                    <Badge className="bg-red-600/10 text-red-500 border-red-500/20 uppercase tracking-[0.2em] text-[10px] font-black italic px-8 py-3 rounded-2xl">
                                        SOTA GENESIS
                                    </Badge>
                                </header>

                                <p className="text-2xl font-bold text-gray-200 leading-relaxed italic border-l-4 border-red-600 pl-8">
                                    "{synthesizedResult.universe.description}"
                                </p>

                                <div className="grid grid-cols-1 md:grid-cols-2 gap-16 pt-10">
                                    <div className="space-y-8">
                                        <h4 className="text-xs font-black uppercase opacity-40 tracking-[0.3em] flex items-center gap-3 border-b border-white/5 pb-4">
                                            <Users className="w-5 h-5 text-red-500" /> Key Entities
                                        </h4>
                                        <div className="space-y-6">
                                            {synthesizedResult.universe.characters.map((char: any) => (
                                                <div key={char.name} className="bg-white/5 border border-white/5 p-8 rounded-3xl flex justify-between items-center group hover:bg-white/10 transition-all hover:translate-x-2">
                                                    <div>
                                                        <span className="font-black text-lg text-white block uppercase italic group-hover:text-red-400 transition-colors">{char.name}</span>
                                                        <span className="text-[10px] text-gray-500 block uppercase font-bold tracking-widest">{char.role}</span>
                                                    </div>
                                                    <div className="text-right">
                                                        <span className="text-[8px] font-black opacity-30 block mb-1">POWER_L</span>
                                                        <Badge className="bg-red-600/20 text-red-400 border-none font-mono text-xs px-4">
                                                            {char.power_level}
                                                        </Badge>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="space-y-8">
                                        <h4 className="text-xs font-black uppercase opacity-40 tracking-[0.3em] flex items-center gap-3 border-b border-white/5 pb-4">
                                            <Film className="w-5 h-5 text-red-500" /> Chronology
                                        </h4>
                                        <div className="space-y-6">
                                            {synthesizedResult.universe.episodes.map((ep: any) => (
                                                <div key={ep.number} className="bg-white/5 border border-white/5 p-8 rounded-3xl space-y-4 group hover:bg-white/10 transition-all">
                                                    <div className="flex justify-between items-center">
                                                        <span className="font-black text-xs text-red-400 block uppercase tracking-[0.2em]">EPISODE_0{ep.number}</span>
                                                        <Zap className="w-3 h-3 opacity-0 group-hover:opacity-100 text-yellow-500 transition-opacity" />
                                                    </div>
                                                    <h5 className="text-lg font-black italic uppercase text-white tracking-tight">{ep.title}</h5>
                                                    <p className="text-xs font-bold text-gray-400 leading-relaxed italic">{ep.summary}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center py-32 opacity-10 text-center border-4 border-dashed border-white/5 rounded-[4rem]">
                            <Globe className="w-48 h-48 mb-12" />
                            <h3 className="text-5xl font-black italic uppercase manga-font mb-4">Nexus de Création</h3>
                            <p className="text-lg font-bold uppercase tracking-[0.4em]">Prêt pour la synthèse d'un nouveau segment de multivers.</p>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default MultiverseLabPage;
