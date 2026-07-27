import React from 'react';
import { motion } from 'framer-motion';
import { Library, Loader2 } from 'lucide-react';
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
    <div className="space-y-5">
      <h2 className="flex items-center gap-3 font-manga text-lg font-black uppercase italic tracking-wide text-[#F4F1E8]">
        <span className="h-4 w-1 flex-none bg-[#E8442B]" aria-hidden />
        Résultats du catalogue
        <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
      </h2>

      {loadingMangas ? (
        <div className="flex flex-col items-center justify-center gap-4 py-24">
          <Loader2 className="h-8 w-8 animate-spin text-[#FDB913]" />
          <p className="text-sm font-semibold text-[#8F94A5]">Parcours du catalogue externe…</p>
        </div>
      ) : mangas.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#F4F1E8]/15 py-24 text-center text-[#8F94A5]">
          <Library className="mb-4 h-12 w-12 text-[#8F94A5]/30" />
          <p className="font-manga text-xl font-black uppercase italic text-[#F4F1E8]/60">
            Aucun manga trouvé
          </p>
          <p className="mt-2 max-w-sm text-sm text-[#8F94A5]/70">
            Choisis une source, ou installe-en une depuis l'onglet Extensions.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 items-start gap-6 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6">
          {mangas.map((manga) => (
            <motion.button
              type="button"
              key={manga.id}
              whileHover={{ y: -4 }}
              onClick={() => onSelectManga(manga)}
              className={`group relative block cursor-pointer overflow-hidden rounded-2xl border bg-[#0F1016] text-left transition-colors ${
                selectedManga?.id === manga.id
                  ? 'border-[#E8442B]'
                  : 'border-[#F4F1E8]/10 hover:border-[#FDB913]/50'
              }`}
            >
              <div className="relative overflow-hidden bg-[#0B0C10]">
                <img
                  src={getProxiedImageUrl(manga.thumbnailUrl)}
                  alt={manga.title}
                  className="block h-auto w-full transition-transform duration-500 group-hover:scale-105"
                  loading="lazy"
                />
                <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#0B0C10] via-transparent to-transparent opacity-60" />
              </div>
              <div className="p-3">
                <h4 className="font-manga line-clamp-2 text-xs font-black uppercase italic leading-tight text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
                  {manga.title}
                </h4>
              </div>
            </motion.button>
          ))}
        </div>
      )}
    </div>
  );
};

export const MangaGrid = React.memo(MangaGridComponent);
