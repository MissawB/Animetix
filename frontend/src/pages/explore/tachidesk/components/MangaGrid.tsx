import React from 'react';
import { motion } from 'framer-motion';
import { Globe, Loader2 } from 'lucide-react';
import type { Manga } from '../types';

interface MangaGridProps {
  mangas: Manga[];
  selectedManga: Manga | null;
  loadingMangas: boolean;
  onSelectManga: (manga: Manga) => void;
  getProxiedImageUrl: (url: string) => string;
}

const MangaGridComponent: React.FC<MangaGridProps> = ({
  mangas,
  selectedManga,
  loadingMangas,
  onSelectManga,
  getProxiedImageUrl,
}) => {
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-black uppercase tracking-widest flex items-center gap-3">
        Résultats du Catalogue
        <span className="h-px bg-white/5 flex-1" />
      </h2>

      {loadingMangas ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-gray-400 text-sm font-semibold">Parcours du catalogue externe...</p>
        </div>
      ) : mangas.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 text-gray-500">
          <Globe className="w-12 h-12 mb-4 opacity-20" />
          <p className="font-bold">Aucun manga trouvé</p>
          <p className="text-sm opacity-60">Sélectionnez une source ou installez-en depuis l'onglet Extensions.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
          {mangas.map((manga) => (
            <motion.div
              key={manga.id}
              whileHover={{ scale: 1.03 }}
              className={`rounded-2xl border transition-all overflow-hidden relative cursor-pointer group bg-[#0d0d1b]/40 backdrop-blur-md ${
                selectedManga?.id === manga.id ? 'border-blue-500 shadow-lg shadow-blue-500/5' : 'border-white/5 hover:border-white/20'
              }`}
              onClick={() => onSelectManga(manga)}
            >
              <div className="aspect-[2/3] overflow-hidden relative bg-black/20">
                <img
                  src={getProxiedImageUrl(manga.thumbnailUrl)}
                  alt={manga.title}
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                  loading="lazy"
                />
              </div>
              <div className="p-3">
                <h4 className="text-xs font-black uppercase line-clamp-2 leading-tight group-hover:text-blue-400 transition-colors">
                  {manga.title}
                </h4>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

export const MangaGrid = React.memo(MangaGridComponent);
