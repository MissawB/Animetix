import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Card } from "../../components/ui/Card";
import { apiClient } from '../../utils/apiClient';
import { Book, Globe, Landmark, TrendingUp, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface MarketEntity {
  definition: string;
  origin: string;
  examples: string;
  impact: string;
}

interface MarketData {
  japanese: {
    publishers: Record<string, MarketEntity>;
    distributors: Record<string, MarketEntity>;
  };
  french: {
    publishers: Record<string, MarketEntity>;
    distributors: Record<string, MarketEntity>;
  };
}

const MarketWikiPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'japanese' | 'french'>('japanese');
  const [activeCategory, setActiveCategory] = useState<'publishers' | 'distributors'>('publishers');
  const [searchTerm, setSearchTerm] = useState('');

  const { data, isLoading } = useQuery<MarketData>({
    queryKey: ['market-wiki'],
    queryFn: () => apiClient('/api/v1/market/wiki/'),
  });

  const getFilteredEntities = () => {
    if (!data) return [];
    const entities = data[activeTab][activeCategory];
    return Object.entries(entities).filter(([name]) => 
      name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const filteredEntities = getFilteredEntities();

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#05050a] text-white p-6 max-w-7xl mx-auto py-16">
        <header className="mb-12 text-center md:text-left">
          <div className="flex items-center justify-center md:justify-start gap-4 mb-4">
            <div className="p-3 bg-anime-accent/20 rounded-2xl border border-anime-accent/30 shadow-[0_0_15px_rgba(var(--accent-rgb),0.2)]">
                <Globe className="w-8 h-8 text-anime-accent" />
            </div>
            <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase">
              WIKI-<span className="text-anime-accent">MARCHÉ</span>
            </h1>
          </div>
          <p className="text-white/60 text-lg max-w-2xl">
            Explorez l'écosystème industriel du manga et de l'animation. Données structurées sur les éditeurs historiques, les diffuseurs majeurs et les comités de production.
          </p>
        </header>

        {/* Tabs & Controls */}
        <div className="flex flex-col md:flex-row gap-6 mb-10 items-center justify-between">
            <div className="flex bg-white/5 p-1.5 rounded-2xl border border-white/10 backdrop-blur-xl">
                <button 
                    onClick={() => setActiveTab('japanese')}
                    className={`px-8 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${activeTab === 'japanese' ? 'bg-anime-accent text-white shadow-lg shadow-anime-accent/20' : 'hover:bg-white/5 opacity-40 hover:opacity-100'}`}
                >
                    Japon (Origines)
                </button>
                <button 
                    onClick={() => setActiveTab('french')}
                    className={`px-8 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${activeTab === 'french' ? 'bg-anime-accent text-white shadow-lg shadow-anime-accent/20' : 'hover:bg-white/5 opacity-40 hover:opacity-100'}`}
                >
                    France (Import)
                </button>
            </div>

            <div className="flex gap-4">
                 <div className="relative">
                    <input 
                        type="text" 
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Rechercher une entité..."
                        className="bg-white/5 border border-white/10 rounded-xl px-10 py-2.5 text-sm outline-none focus:border-anime-accent transition-all w-64"
                    />
                    <Search className="absolute left-3 top-3 w-4 h-4 opacity-30" />
                 </div>
                 
                 <div className="flex bg-white/5 p-1 rounded-xl border border-white/10">
                    <button 
                        onClick={() => setActiveCategory('publishers')}
                        className={`p-2 rounded-lg transition-all ${activeCategory === 'publishers' ? 'bg-white/10 text-white' : 'text-white/30 hover:text-white'}`}
                        title="Éditeurs"
                    >
                        <Book className="w-5 h-5" />
                    </button>
                    <button 
                        onClick={() => setActiveCategory('distributors')}
                        className={`p-2 rounded-lg transition-all ${activeCategory === 'distributors' ? 'bg-white/10 text-white' : 'text-white/30 hover:text-white'}`}
                        title="Diffuseurs / Studios"
                    >
                        <Landmark className="w-5 h-5" />
                    </button>
                 </div>
            </div>
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatePresence mode="popLayout">
                {isLoading ? (
                    Array(6).fill(0).map((_, i) => (
                        <div key={i} className="h-64 bg-white/5 rounded-3xl animate-pulse border border-white/5" />
                    ))
                ) : filteredEntities.length > 0 ? (
                    filteredEntities.map(([name, details]) => (
                        <motion.div
                            key={name}
                            layout
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95 }}
                            transition={{ duration: 0.3 }}
                        >
                            <Card padding="none" className="group overflow-hidden bg-navy-900/40 border-white/5 hover:border-anime-accent/50 transition-all h-full flex flex-col">
                                <div className="p-6 border-b border-white/5 bg-white/[0.02]">
                                    <div className="flex items-center justify-between mb-2">
                                        <h2 className="text-xl font-black italic tracking-tighter uppercase group-hover:text-anime-accent transition-colors">
                                            {name}
                                        </h2>
                                        <TrendingUp className="w-4 h-4 opacity-20 group-hover:opacity-100 group-hover:text-anime-accent transition-all" />
                                    </div>
                                    <p className="text-xs text-white/40 font-bold uppercase tracking-widest leading-tight">
                                        {activeCategory === 'publishers' ? 'Maison d\'Édition' : 'Diffuseur / Production'}
                                    </p>
                                </div>

                                <div className="p-6 space-y-5 flex-grow">
                                    <div className="space-y-1.5">
                                        <span className="text-[10px] font-black text-anime-accent uppercase tracking-widest block">Définition</span>
                                        <p className="text-sm text-white/70 leading-relaxed italic">"{details.definition}"</p>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="space-y-1.5">
                                            <span className="text-[10px] font-black opacity-30 uppercase tracking-widest block">Origine</span>
                                            <p className="text-[11px] text-white/50">{details.origin}</p>
                                        </div>
                                        <div className="space-y-1.5">
                                            <span className="text-[10px] font-black opacity-30 uppercase tracking-widest block">Impact</span>
                                            <p className="text-[11px] text-white/50">{details.impact}</p>
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        <span className="text-[10px] font-black opacity-30 uppercase tracking-widest block">Œuvres Clés</span>
                                        <div className="text-[11px] text-white/60 bg-black/40 p-3 rounded-xl border border-white/5 leading-relaxed">
                                            {details.examples.split(', ').map((ex, idx) => (
                                                <span key={idx} className={`${idx > 0 ? 'before:content-["•"] before:mx-2 before:opacity-20' : ''}`}>
                                                    {ex.replace(/\*/g, '')}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </Card>
                        </motion.div>
                    ))
                ) : (
                    <div className="col-span-full py-20 text-center">
                        <Globe className="w-12 h-12 opacity-10 mx-auto mb-4" />
                        <p className="text-white/30 font-black italic uppercase tracking-widest">Aucune entité trouvée pour "{searchTerm}"</p>
                    </div>
                )}
            </AnimatePresence>
        </div>

        {/* Info Footer */}
        <footer className="mt-16 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between items-center gap-6 opacity-30">
            <p className="text-[10px] font-bold uppercase tracking-widest">
                Source: Animetix MLOps Knowledge Ingestion Pipeline v2.4
            </p>
            <div className="flex gap-8 text-[10px] font-bold uppercase tracking-widest">
                <span>15 Éditeurs JP</span>
                <span>10 Éditeurs FR</span>
                <span>20 Studios & Diffuseurs</span>
            </div>
        </footer>
      </div>
    </AnimatedPage>
  );
};

export default MarketWikiPage;
