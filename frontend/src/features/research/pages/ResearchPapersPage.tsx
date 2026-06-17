import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BookOpen, Brain, Cpu, Database, ShieldCheck, 
  Layers, ExternalLink, Search, Info,
  Atom, Video, Radio, Zap
} from 'lucide-react';
import { researchPapers } from '../data/papers';

const CATEGORIES = [
  { id: 'all', label: 'Tous les papiers', icon: <BookOpen className="w-4 h-4" /> },
  { id: 'reasoning', label: 'Raisonnement & CoT', icon: <Brain className="w-4 h-4" /> },
  { id: 'agents', label: 'Agents & Jeux', icon: <Cpu className="w-4 h-4" /> },
  { id: 'multimodal', label: 'Multimodalité', icon: <Video className="w-4 h-4" /> },
  { id: 'rag', label: 'RAG & Graphes', icon: <Database className="w-4 h-4" /> },
  { id: 'mlops', label: 'MLOps & Sécurité', icon: <ShieldCheck className="w-4 h-4" /> },
  { id: 'advanced', label: 'Sciences Avancées', icon: <Atom className="w-4 h-4" /> },
];

const ResearchPapersPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredPapers = researchPapers.filter(paper => {
    const matchesTab = activeTab === 'all' || paper.category === activeTab;
    const matchesSearch = paper.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          paper.keyConcept.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTab && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-surface-bg pt-32 pb-20 px-6 md:px-10 transition-colors duration-500">
      <div className="max-w-7xl mx-auto">
        
        {/* Header Section */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-yellow-400/10 dark:bg-yellow-400/5 border border-yellow-400/20 rounded-full text-yellow-600 dark:text-yellow-400 text-xs font-black uppercase tracking-widest mb-6">
            <Zap className="w-4 h-4 fill-current" /> State-of-the-Art Architecture
          </div>
          <h1 className="manga-font text-5xl md:text-7xl mb-6 text-surface-text tracking-tighter">
            LABO DE <span className="text-yellow-400">RECHERCHE</span>
          </h1>
          <p className="text-gray-600 dark:text-gray-400 max-w-2xl mx-auto text-lg leading-relaxed italic">
            "L'architecture d'Animetix n'est pas le fruit du hasard. Découvrez les fondations académiques et les publications scientifiques qui propulsent nos algorithmes."
          </p>
        </motion.div>

        {/* Search & Filter Bar */}
        <div className="mb-12 flex flex-col xl:flex-row gap-6 items-center justify-between sticky top-24 z-40 bg-surface-bg/80 backdrop-blur-xl p-4 rounded-3xl border border-surface-text/5 shadow-2xl">
          <div className="relative w-full xl:w-96 shrink-0">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input 
              type="text"
              placeholder="Rechercher un concept ou un papier..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-surface-card dark:bg-black/40 border-2 border-transparent focus:border-yellow-400 rounded-2xl py-3 pl-12 pr-4 text-surface-text transition-all outline-none shadow-sm"
            />
          </div>
          
          <div className="flex gap-2 overflow-x-auto pb-2 xl:pb-0 no-scrollbar w-full xl:w-auto justify-start xl:justify-end">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setActiveTab(cat.id)}
                className={`flex items-center gap-2 px-5 py-2.5 rounded-xl whitespace-nowrap text-xs font-black transition-all ${
                  activeTab === cat.id 
                    ? 'bg-yellow-400 text-black shadow-lg scale-105' 
                    : 'bg-surface-card dark:bg-white/5 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/10'
                }`}
              >
                {cat.icon}
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Papers Grid */}
        <motion.div 
          layout
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8"
        >
          <AnimatePresence mode="popLayout">
            {filteredPapers.map((paper, index) => (
              <motion.div
                key={paper.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                className="group relative bg-white dark:bg-surface-card/40 rounded-[2.5rem] p-8 border border-surface-text/5 dark:border-white/5 shadow-xl hover:shadow-2xl transition-all hover:-translate-y-2 flex flex-col overflow-hidden"
              >
                {/* Background Decoration */}
                <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-yellow-400/10 rounded-full blur-3xl group-hover:bg-yellow-400/20 transition-colors" />
                
                <div className="mb-6 flex justify-between items-start relative z-10">
                  <div className="p-3 bg-gray-50 dark:bg-black/30 rounded-2xl border border-black/5 dark:border-white/10">
                    {paper.category === 'reasoning' && <Brain className="w-6 h-6 text-pink-500" />}
                    {paper.category === 'agents' && <Cpu className="w-6 h-6 text-cyan-500" />}
                    {paper.category === 'multimodal' && <Video className="w-6 h-6 text-purple-500" />}
                    {paper.category === 'rag' && <Database className="w-6 h-6 text-emerald-500" />}
                    {paper.category === 'mlops' && <ShieldCheck className="w-6 h-6 text-blue-500" />}
                    {paper.category === 'advanced' && <Atom className="w-6 h-6 text-orange-500" />}
                  </div>
                  <a 
                    href={paper.url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="p-2 text-gray-400 hover:text-yellow-400 transition-colors bg-white dark:bg-black/20 rounded-xl"
                  >
                    <ExternalLink className="w-5 h-5" />
                  </a>
                </div>

                <div className="flex-grow relative z-10">
                  <span className="text-[10px] font-bold text-yellow-600 dark:text-yellow-400 uppercase tracking-widest mb-2 block">
                    {paper.source}
                  </span>
                  <h3 className="manga-font text-xl leading-tight mb-4 text-black dark:text-white group-hover:text-yellow-400 transition-colors">
                    {paper.title}
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-[10px] font-black uppercase text-gray-400 mb-1 flex items-center gap-1">
                        <Info className="w-3 h-3" /> Concept Clé
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-300 italic">
                        {paper.keyConcept}
                      </p>
                    </div>
                    
                    <div className="bg-yellow-400/5 dark:bg-black/30 p-4 rounded-2xl border border-yellow-400/10">
                      <h4 className="text-[10px] font-black uppercase text-yellow-600 dark:text-yellow-400 mb-2 flex items-center gap-1">
                        <Layers className="w-3 h-3" /> Implémentation Animetix
                      </h4>
                      <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed font-medium">
                        {paper.implementation}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Bottom Number */}
                <div className="absolute bottom-6 right-8 text-5xl font-black opacity-[0.03] dark:opacity-[0.05] pointer-events-none select-none">
                  #{index + 1}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>

        {/* Empty State */}
        {filteredPapers.length === 0 && (
          <div className="py-40 text-center">
            <div className="w-20 h-20 bg-gray-100 dark:bg-white/5 rounded-full flex items-center justify-center mx-auto mb-6">
              <Search className="w-10 h-10 text-gray-300" />
            </div>
            <p className="text-gray-500 font-bold uppercase tracking-widest">Aucun papier trouvé pour cette recherche.</p>
          </div>
        )}

        {/* Methodology Notice */}
        <div className="mt-20 p-10 bg-black text-white rounded-[3rem] shadow-2xl relative overflow-hidden group">
           <div className="absolute top-0 right-0 w-64 h-64 bg-yellow-400/20 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2" />
           <div className="relative z-10">
              <h2 className="manga-font text-3xl mb-4 tracking-tighter">PROTOCOLE DE <span className="text-yellow-400">VEILLE</span></h2>
              <p className="text-gray-400 leading-relaxed max-w-3xl text-sm italic">
                "Notre équipe d'ingénieurs maintient une veille technologique constante. Chaque semaine, de nouveaux papiers de recherche sont analysés, testés dans nos 'Ghost Labs', puis intégrés dans le moteur Animetix s'ils prouvent une amélioration significative de l'expérience utilisateur ou de la sécurité du système."
              </p>
              <div className="mt-8 flex flex-wrap gap-4">
                 <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-full border border-white/10 text-[10px] font-black tracking-widest uppercase">
                    <Radio className="w-4 h-4 text-red-500 animate-pulse" /> Live Monitoring 2026
                 </div>
                 <div className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-full border border-white/10 text-[10px] font-black tracking-widest uppercase text-yellow-400">
                    100% Academic Compliance
                 </div>
              </div>
           </div>
        </div>

      </div>
    </div>
  );
};

export default ResearchPapersPage;
