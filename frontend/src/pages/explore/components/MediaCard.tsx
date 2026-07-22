import React from 'react';
import { motion } from 'framer-motion';
import { Info, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiClient } from '../../../utils/apiClient';

export type FeedItem = {
  id: string;
  title: string;
  title_native?: string;
  title_english?: string;
  media_type: string;
  image?: string;
  synopsis_fr?: string;
  year?: number;
  popularity?: number;
  rating?: number;
  genres?: string[];
};

export const MediaCard: React.FC<{ item: FeedItem }> = ({ item }) => {
  const [saved, setSaved] = React.useState(false);
  const isManga = item.media_type === 'Manga';
  const originalTitle = [item.title_native, item.title_english].find(
    (t) => t && t.trim() !== '' && t.toLowerCase() !== item.title.toLowerCase(),
  );

  const toggleFavorite = async () => {
    try {
      await apiClient(`/api/v1/media/Manga/${item.id}/favorite/`, {
        method: 'POST',
        body: JSON.stringify({ status: 'plan_to_read' }),
      });
      setSaved(true);
    } catch {
      // toast déjà géré par apiClient
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.04, zIndex: 10 }}
      className="group relative aspect-[2/3] w-48 flex-none cursor-pointer overflow-hidden rounded-[4px] ring-1 ring-[#F4F1E8]/10 md:w-56"
    >
      <img
        src={item.image || 'https://via.placeholder.com/300x450'}
        alt={item.title}
        className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
        loading="lazy"
        decoding="async"
      />

      {/* Persistent meta strip (s'efface au survol au profit de l'overlay) */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-3 transition-opacity duration-300 group-hover:opacity-0 group-focus-within:opacity-0">
        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest">
          {item.rating != null && (
            <span className="flex items-center gap-1 text-[#FDB913]">
              <Star size={10} fill="currentColor" /> {item.rating.toFixed(1)}
            </span>
          )}
          {item.year != null && <span className="text-[#F4F1E8]/80">{item.year}</span>}
          <span className="ml-auto rounded-[2px] border border-[#F4F1E8]/25 px-1.5 py-0.5 text-[#F4F1E8]/75">
            {item.media_type.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Hover overlay */}
      <div className="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-[#0B0C10] via-[#0B0C10]/40 to-transparent p-4 opacity-0 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100">
        <h4 className="font-manga text-sm font-black uppercase italic leading-tight text-[#F4F1E8]">
          {item.title}
        </h4>
        {originalTitle && (
          <p className="mt-0.5 text-[11px] leading-snug text-[#8F94A5]">{originalTitle}</p>
        )}
        <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] font-black uppercase tracking-widest">
          {item.rating != null && (
            <span className="flex items-center gap-1 text-[#FDB913]">
              <Star size={10} fill="currentColor" /> {item.rating.toFixed(1)}
            </span>
          )}
          {item.year != null && <span className="text-[#F4F1E8]/80">{item.year}</span>}
          {(item.genres ?? []).slice(0, 2).map((genre) => (
            <span key={genre} className="font-bold text-[#8F94A5]">
              {genre}
            </span>
          ))}
        </div>
        <div className="mt-3 flex gap-2">
          <Link
            to={`/media/${item.media_type}/${item.id}/`}
            aria-label="Voir la fiche"
            className="rounded-full bg-[#F4F1E8] p-2 text-[#0B0C10] transition-colors hover:bg-[#FDB913] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
          >
            <Info size={14} />
          </Link>
          {isManga && (
            <button
              type="button"
              onClick={toggleFavorite}
              aria-label="Ajouter aux favoris"
              className={`rounded-full p-2 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] ${
                saved
                  ? 'bg-[#FDB913]/20 text-[#FDB913]'
                  : 'bg-[#0B0C10]/80 text-[#F4F1E8] hover:bg-[#0B0C10]'
              }`}
            >
              <Star size={14} fill={saved ? 'currentColor' : 'none'} />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
};
