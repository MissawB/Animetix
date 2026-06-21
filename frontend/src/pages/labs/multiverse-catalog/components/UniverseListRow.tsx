import React from 'react';
import { Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { Badge } from '../../../../components/ui/Badge';
import { getGenreAccent } from '../genre';
import { GenreIcon } from './GenreIcon';
import type { Universe } from '../types';

// ─── Universe Row (List) ─────────────────────────────────────────────
const UniverseListRow: React.FC<{ universe: Universe; index: number; onSelect: (u: Universe) => void }> = ({ universe, index, onSelect }) => {
  const accent = getGenreAccent(universe.genre);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.03, duration: 0.3 }}
      onClick={() => onSelect(universe)}
      className="flex items-center gap-6 p-5 bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 hover:border-white/10 rounded-2xl cursor-pointer transition-all duration-300 group"
    >
      {/* Icon */}
      <div className={`shrink-0 p-4 rounded-xl bg-white/5 group-hover:bg-white/10 transition-colors`}>
        <GenreIcon genre={universe.genre} className={`w-7 h-7 ${accent}`} />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <h3 className="text-sm font-black italic manga-font uppercase truncate group-hover:text-white transition-colors">
            {universe.name}
          </h3>
          <Badge variant="neutral" className={`text-[8px] uppercase font-black ${accent} shrink-0`}>
            {universe.genre}
          </Badge>
          <div className="flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 shrink-0">
            <Sparkles className="w-2 h-2 text-emerald-400" />
            <span className="text-[7px] font-black text-emerald-400 uppercase">Synthétique</span>
          </div>
        </div>
        <p className="text-[10px] font-bold opacity-30 uppercase tracking-wider truncate">
          {universe.description || universe.cosmology || 'Univers généré par intelligence artificielle'}
        </p>
      </div>

      {/* Stats */}
      <div className="shrink-0 flex items-center gap-6">
        <div className="text-right">
          <p className="text-[8px] font-black uppercase opacity-20 mb-0.5">Entités</p>
          <p className={`text-lg font-black italic manga-font ${accent}`}>{universe.character_count}</p>
        </div>
        <div className="shrink-0 flex -space-x-1.5">
          {universe.characters.slice(0, 4).map((c, i) => (
            <div
              key={i}
              className="w-7 h-7 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-[9px] font-black opacity-60"
              title={c.name}
            >
              {c.name.charAt(0)}
            </div>
          ))}
        </div>
      </div>
    </motion.div>
  );
};

export default React.memo(UniverseListRow);
