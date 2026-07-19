import React from 'react';
import { motion } from 'framer-motion';
import { Info, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiClient } from '../../../utils/apiClient';

export type FeedItem = {
  id: string;
  title: string;
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
      whileHover={{ scale: 1.05, zIndex: 10 }}
      className="flex-none w-48 md:w-56 aspect-[2/3] rounded-xl overflow-hidden relative group cursor-pointer"
    >
      <img
        src={item.image || 'https://via.placeholder.com/300x450'}
        alt={item.title}
        className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        loading="lazy"
        decoding="async"
      />

      {/* Persistent meta strip */}
      <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-3 pointer-events-none">
        <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest">
          {item.rating != null && (
            <span className="flex items-center gap-1 text-yellow-400">
              <Star size={10} fill="currentColor" /> {item.rating.toFixed(1)}
            </span>
          )}
          {item.year != null && <span className="text-gray-300">{item.year}</span>}
          <span className="ml-auto px-1.5 py-0.5 bg-white/10 rounded text-gray-200">
            {item.media_type.toUpperCase()}
          </span>
        </div>
      </div>

      {/* Hover overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
        <h4 className="text-sm font-black uppercase italic leading-tight mb-1">{item.title}</h4>
        {item.genres && item.genres.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-2">
            {item.genres.slice(0, 2).map((genre) => (
              <span key={genre} className="text-[9px] uppercase tracking-widest text-gray-400">
                {genre}
              </span>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <Link
            to={`/media/${item.media_type.toLowerCase()}/${item.id}/`}
            aria-label="Voir la fiche"
            className="p-2 bg-white text-black rounded-full hover:bg-gray-200 transition-colors"
          >
            <Info size={14} />
          </Link>
          {isManga && (
            <button
              onClick={toggleFavorite}
              aria-label="Ajouter aux favoris"
              className="p-2 bg-gray-800/80 text-white rounded-full hover:bg-gray-700 transition-colors"
            >
              <Star size={14} fill={saved ? 'currentColor' : 'none'} />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
};
