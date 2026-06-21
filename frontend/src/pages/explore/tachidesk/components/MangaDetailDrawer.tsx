import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen, X, Loader2, ChevronRight, Heart, ChevronDown } from 'lucide-react';
import type { Manga, Chapter } from '../types';

interface MangaDetailDrawerProps {
  selectedManga: Manga;
  chapters: Chapter[];
  loadingDetails: boolean;
  importStatus: string | null;
  importingChapter: string | null;
  onClose: () => void;
  onReadChapter: (chapter: Chapter) => void;
  getProxiedImageUrl: (url: string) => string;
  isFavorited?: boolean;
  favoriteStatus?: 'reading' | 'completed' | 'plan_to_read' | null;
  togglingFavorite?: boolean;
  onToggleFavorite?: () => void;
  onUpdateFavoriteStatus?: (status: 'reading' | 'completed' | 'plan_to_read') => void;
}

const MangaDetailDrawerComponent: React.FC<MangaDetailDrawerProps> = ({
  selectedManga,
  chapters,
  loadingDetails,
  importStatus,
  importingChapter,
  onClose,
  onReadChapter,
  getProxiedImageUrl,
  isFavorited = false,
  favoriteStatus = null,
  togglingFavorite = false,
  onToggleFavorite,
  onUpdateFavoriteStatus,
}) => {
  return (
    <motion.aside
      initial={{ x: 400, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 400, opacity: 0 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="w-[400px] border-l border-white/5 bg-[#080811]/90 backdrop-blur-2xl p-8 flex flex-col h-full overflow-hidden"
    >
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-black uppercase tracking-widest text-blue-500 flex items-center gap-2">
          <BookOpen className="w-4 h-4" /> Détails de l'œuvre
        </h3>
        <button
          onClick={onClose}
          className="p-1.5 hover:bg-white/5 rounded-full transition-colors"
        >
          <X className="w-5 h-5 text-gray-400 hover:text-white" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto space-y-6 pr-2 -mr-2">
        <div className="flex gap-4">
          <div className="w-28 aspect-[2/3] rounded-xl overflow-hidden flex-shrink-0 bg-white/5 border border-white/10">
            <img
              src={getProxiedImageUrl(selectedManga.thumbnailUrl)}
              alt={selectedManga.title}
              className="w-full h-full object-cover"
            />
          </div>
          <div className="flex-1 flex flex-col justify-center">
            <h2 className="text-lg font-black uppercase leading-tight italic tracking-tight mb-3">
              {selectedManga.title}
            </h2>
            <div className="flex gap-2 flex-wrap items-center mt-1">
              {onToggleFavorite && (
                <button
                  onClick={onToggleFavorite}
                  disabled={togglingFavorite}
                  className={`px-3 py-1.5 rounded-xl border text-[10px] font-black uppercase italic tracking-wider flex items-center gap-1.5 transition-all ${
                    isFavorited
                      ? 'bg-blue-500/10 border-blue-500/30 text-blue-400 hover:bg-blue-500/20'
                      : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  {togglingFavorite ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Heart className={`w-3 h-3 ${isFavorited ? 'fill-current text-blue-400' : ''}`} />
                  )}
                  {isFavorited ? 'Suivi' : 'Suivre'}
                </button>
              )}

              {isFavorited && onUpdateFavoriteStatus && (
                <div className="relative">
                  <select
                    value={favoriteStatus || 'plan_to_read'}
                    disabled={togglingFavorite}
                    onChange={e => onUpdateFavoriteStatus(e.target.value as any)}
                    className="pl-3 pr-8 py-1.5 bg-white/5 hover:bg-white/10 text-white/80 text-[10px] font-black uppercase tracking-wider rounded-xl border border-white/5 outline-none cursor-pointer appearance-none transition-colors"
                  >
                    <option value="reading" className="bg-[#080811] text-white">En cours</option>
                    <option value="plan_to_read" className="bg-[#080811] text-white">À lire</option>
                    <option value="completed" className="bg-[#080811] text-white">Terminé</option>
                  </select>
                  <ChevronDown className="w-3 h-3 text-white/40 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                </div>
              )}
            </div>
          </div>
        </div>

        {importStatus && (
          <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-xl flex items-center gap-3 text-blue-400 text-xs font-semibold">
            <Loader2 className="w-4 h-4 animate-spin flex-shrink-0" />
            <div>{importStatus}</div>
          </div>
        )}

        {/* Chapters List */}
        <div className="space-y-3">
          <h4 className="text-xs font-black uppercase tracking-widest text-gray-500 flex items-center justify-between">
            <span>Chapitres Disponibles</span>
            <span className="text-[10px] bg-white/5 text-gray-400 px-2 py-0.5 rounded-full">
              {chapters.length} chapitres
            </span>
          </h4>

          {loadingDetails ? (
            <div className="flex flex-col items-center justify-center py-12 gap-3 text-gray-400">
              <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
              <p className="text-xs font-medium">Récupération des chapitres...</p>
            </div>
          ) : chapters.length === 0 ? (
            <div className="text-center py-12 text-gray-500 text-xs font-semibold border border-dashed border-white/5 rounded-2xl">
              Aucun chapitre indexé pour ce manga.
            </div>
          ) : (
            <div className="space-y-2 max-h-[350px] overflow-y-auto pr-1">
              {chapters.map((ch) => (
                <div
                  key={ch.id}
                  className="p-3 bg-[#0d0d1b]/80 border border-white/5 hover:border-white/15 rounded-xl flex items-center justify-between group transition-all"
                >
                  <div className="flex flex-col min-w-0 pr-4">
                    <span className="text-xs font-bold text-gray-200 line-clamp-1 group-hover:text-blue-400 transition-colors">
                      {ch.name}
                    </span>
                    <span className="text-[9px] text-gray-500 font-medium">
                      Numéro {ch.chapterNumber}
                    </span>
                  </div>

                  <button
                    onClick={() => onReadChapter(ch)}
                    disabled={!!importingChapter}
                    className="px-3 py-1.5 bg-blue-500/10 hover:bg-blue-600 border border-blue-500/20 text-blue-400 hover:text-white rounded-lg text-[10px] font-black uppercase italic tracking-wider flex items-center gap-1 hover:scale-[1.03] transition-all disabled:opacity-50"
                  >
                    {importingChapter === ch.id ? (
                      <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                      <>
                        Lire <ChevronRight className="w-3 h-3" />
                      </>
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </motion.aside>
  );
};

export const MangaDetailDrawer = React.memo(MangaDetailDrawerComponent);
