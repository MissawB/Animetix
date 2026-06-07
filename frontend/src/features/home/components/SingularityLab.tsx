import React from 'react';
import { Link } from 'react-router-dom';
import { Zap, ArrowRight } from 'lucide-react';
import { useGameModes } from '../data/useGameModes';

export const SingularityLab: React.FC = () => {
  const { isEn } = useGameModes();

  return (
    <section className="py-24 text-center border-t border-black/5 dark:border-white/5">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-600/10 text-red-500 text-[10px] font-black uppercase tracking-widest mb-4">
          <Zap className="w-3 h-3" /> NIVEAU OMEGA
        </div>
        <h2 className="text-5xl md:text-7xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
          SINGULARITY <span className="text-red-600 text-glow">LABS</span>
        </h2>
        <p className="text-lg md:text-xl font-bold opacity-40 uppercase tracking-[0.3em] leading-relaxed italic">
          {isEn ? 'Explore the boundaries of generative AI and pure cognition.' : "Explorez la frontière entre l'IA générative et la cognition pure."}
        </p>
        <Link 
          to="/lab/" 
          className="mt-12 group bg-black text-white hover:bg-red-600 py-6 px-16 rounded-[2rem] font-black italic text-xl uppercase shadow-2xl hover:scale-105 active:scale-95 transition-all inline-flex items-center gap-4 no-underline"
        >
          INITIALISER L'ACCÈS <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
        </Link>
      </div>
    </section>
  );
};
