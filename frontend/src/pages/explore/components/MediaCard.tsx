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
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
        <h4 className="text-sm font-black uppercase italic leading-tight mb-2">{item.title}</h4>
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
