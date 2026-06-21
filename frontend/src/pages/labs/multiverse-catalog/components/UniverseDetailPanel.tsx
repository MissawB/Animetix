import React from 'react';
import { Link } from 'react-router-dom';
import {
  Sparkles,
  Users,
  X,
  Network,
  Orbit,
  BookOpen,
  Download,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Badge } from '../../../../components/ui/Badge';
import { Button } from '../../../../components/ui/Button';
import { getGenreAccent, getGenreColor } from '../genre';
import { GenreIcon } from './GenreIcon';
import type { Universe } from '../types';

// ─── Detail Panel ────────────────────────────────────────────────────
const UniverseDetailPanel: React.FC<{ universe: Universe; onClose: () => void }> = ({ universe, onClose }) => {
  const accent = getGenreAccent(universe.genre);
  const colorClasses = getGenreColor(universe.genre);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, y: 20 }}
        animate={{ scale: 1, y: 0 }}
        exit={{ scale: 0.95, y: 10 }}
        transition={{ type: 'spring', damping: 25, stiffness: 300 }}
        className={`relative w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-[#0a0a14] border ${colorClasses.split(' ').pop()} rounded-3xl shadow-2xl custom-scrollbar`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`p-10 bg-gradient-to-br ${colorClasses} relative overflow-hidden`}>
          <div className="absolute -top-10 -right-10 opacity-10">
            <GenreIcon genre={universe.genre} className="w-40 h-40" />
          </div>
          <button onClick={onClose} className="absolute top-6 right-6 p-2 rounded-full bg-black/30 hover:bg-black/50 transition-colors">
            <X className="w-5 h-5 text-white/60" />
          </button>

          <div className="flex items-center gap-2 mb-4">
            <Badge variant="primary" className={`${accent} bg-black/30 border-white/10 text-[9px]`}>
              {universe.genre}
            </Badge>
            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
              <Sparkles className="w-2.5 h-2.5 text-emerald-400" />
              <span className="text-[8px] font-black text-emerald-400 uppercase">Généré par IA</span>
            </div>
          </div>

          <h2 className="text-4xl font-black italic manga-font uppercase tracking-tight text-white leading-none relative z-10">
            {universe.name}
          </h2>
        </div>

        {/* Body */}
        <div className="p-10 space-y-8">
          {/* Description */}
          {universe.description && (
            <section>
              <h3 className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 mb-3 flex items-center gap-2">
                <BookOpen className="w-3.5 h-3.5" /> Synopsis
              </h3>
              <p className="text-sm font-bold leading-relaxed text-gray-300 italic">
                {universe.description}
              </p>
            </section>
          )}

          {/* Cosmology */}
          {universe.cosmology && (
            <section>
              <h3 className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 mb-3 flex items-center gap-2">
                <Orbit className="w-3.5 h-3.5" /> Cosmologie
              </h3>
              <div className="p-6 rounded-2xl bg-white/[0.03] border border-white/5">
                <p className="text-sm font-bold leading-relaxed text-gray-400">
                  {universe.cosmology}
                </p>
              </div>
            </section>
          )}

          {/* Characters */}
          {universe.characters.length > 0 && (
            <section>
              <h3 className="text-[10px] font-black uppercase tracking-[0.2em] opacity-30 mb-4 flex items-center gap-2">
                <Users className="w-3.5 h-3.5" /> Entités du Nexus ({universe.character_count})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {universe.characters.map((c, i) => (
                  <div key={i} className="flex items-center gap-4 p-4 rounded-xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.05] transition-colors">
                    <div className={`w-10 h-10 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-sm font-black ${accent}`}>
                      {c.name.charAt(0)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-black uppercase text-white/80 truncate">{c.name}</p>
                      <p className="text-[9px] font-bold opacity-30 truncate">{c.role}</p>
                    </div>
                    {c.power_level > 0 && (
                      <div className="shrink-0 text-right">
                        <p className="text-[8px] font-black uppercase opacity-20">PWR</p>
                        <p className={`text-sm font-black italic ${accent}`}>{c.power_level.toLocaleString()}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* CTA */}
          <div className="pt-6 border-t border-white/5 flex gap-4">
            <Link to="/lab/multiverse/" className="flex-1">
              <Button className="w-full bg-cyan-600 hover:bg-cyan-500 text-white py-4 rounded-xl font-black italic uppercase shadow-lg shadow-cyan-900/20">
                <Network className="w-4 h-4 mr-2" /> Explorer dans le Nexus
              </Button>
            </Link>
            <Button
              onClick={() => {
                window.open(`/api/v1/multiverse/${encodeURIComponent(universe.name)}/export-pdf/`, '_blank');
              }}
              className="bg-white/5 hover:bg-white/10 text-white border border-white/10 py-4 px-6 rounded-xl font-black italic uppercase shrink-0 flex items-center justify-center"
            >
              <Download className="w-4 h-4 mr-2" /> Exporter PDF
            </Button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default React.memo(UniverseDetailPanel);
