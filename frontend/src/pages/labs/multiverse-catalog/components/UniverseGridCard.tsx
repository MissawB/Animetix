import React from 'react';
import { Sparkles, Users } from 'lucide-react';
import { motion } from 'framer-motion';
import { Card } from '../../../../components/ui/Card';
import { Badge } from '../../../../components/ui/Badge';
import { getGenreColor, getGenreAccent } from '../genre';
import { GenreIcon } from './GenreIcon';
import type { Universe } from '../types';

// ─── Universe Card (Grid) ────────────────────────────────────────────
const UniverseGridCard: React.FC<{ universe: Universe; index: number; onSelect: (u: Universe) => void }> = ({ universe, index, onSelect }) => {
  const colorClasses = getGenreColor(universe.genre);
  const accent = getGenreAccent(universe.genre);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.4 }}
      layout
    >
      <Card
        padding="none"
        className={`group cursor-pointer bg-gradient-to-br ${colorClasses} border hover:scale-[1.02] hover:shadow-2xl hover:shadow-black/40 transition-all duration-500 overflow-hidden h-full flex flex-col`}
        onClick={() => onSelect(universe)}
      >
        {/* Visual header area */}
        <div className="relative h-44 bg-black/40 flex items-center justify-center overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(255,255,255,0.03),transparent_70%)]" />

          {/* Floating particles */}
          <div className="absolute top-4 right-6 w-2 h-2 rounded-full bg-white/10 animate-pulse" />
          <div className="absolute bottom-8 left-10 w-1.5 h-1.5 rounded-full bg-white/5 animate-pulse" style={{ animationDelay: '1s' }} />
          <div className="absolute top-12 left-8 w-1 h-1 rounded-full bg-white/10 animate-pulse" style={{ animationDelay: '0.5s' }} />

          <GenreIcon genre={universe.genre} className={`w-16 h-16 ${accent} opacity-20 group-hover:opacity-40 group-hover:scale-110 transition-all duration-700`} />

          {/* Genre badge */}
          <div className="absolute top-4 left-4">
            <Badge variant="neutral" className={`text-[8px] uppercase font-black tracking-widest ${accent} bg-black/50 backdrop-blur-sm border-white/10`}>
              {universe.genre}
            </Badge>
          </div>

          {/* Synthetic badge */}
          <div className="absolute top-4 right-4">
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <Sparkles className="w-2.5 h-2.5 text-emerald-400" />
              <span className="text-[8px] font-black text-emerald-400 uppercase">IA</span>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-5 flex-1 flex flex-col">
          <h3 className="text-base font-black italic manga-font uppercase mb-2 group-hover:text-white transition-colors leading-tight truncate">
            {universe.name}
          </h3>
          <p className="text-[10px] font-bold opacity-40 uppercase leading-relaxed tracking-wider line-clamp-3 mb-4 flex-1">
            {universe.description || universe.cosmology || 'Univers synthétique généré par IA'}
          </p>

          {/* Characters preview */}
          <div className="flex items-center justify-between pt-3 border-t border-white/5">
            <div className="flex items-center gap-2">
              <Users className="w-3.5 h-3.5 opacity-30" />
              <span className="text-[9px] font-black uppercase opacity-40">{universe.character_count} entités</span>
            </div>
            {universe.characters.length > 0 && (
              <div className="flex -space-x-1.5">
                {universe.characters.slice(0, 3).map((c, i) => (
                  <div
                    key={i}
                    className={`w-6 h-6 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-[8px] font-black ${accent}`}
                    title={c.name}
                  >
                    {c.name.charAt(0)}
                  </div>
                ))}
                {universe.character_count > 3 && (
                  <div className="w-6 h-6 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-[8px] font-bold opacity-30">
                    +{universe.character_count - 3}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </Card>
    </motion.div>
  );
};

export default React.memo(UniverseGridCard);
