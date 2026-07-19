import React from 'react';
import { Globe, MapPin, Search } from 'lucide-react';
import { Link } from 'react-router-dom';

const MEDIA_TYPES = ['Anime', 'Manga', 'Game', 'Movie'];

interface ExploreToolbarProps {
  mediaType: string;
  onMediaTypeChange: (type: string) => void;
  query: string;
  onQueryChange: (query: string) => void;
  genres: string[];
  selectedGenres: Set<string>;
  onToggleGenre: (genre: string) => void;
}

export const ExploreToolbar: React.FC<ExploreToolbarProps> = ({
  mediaType,
  onMediaTypeChange,
  query,
  onQueryChange,
  genres,
  selectedGenres,
  onToggleGenre,
}) => (
  <div className="sticky top-0 z-30 bg-[#0a0a0a]/90 backdrop-blur border-b border-white/5 py-4 space-y-4">
    <div className="flex flex-wrap justify-between items-center gap-4">
      <div className="flex gap-6">
        {MEDIA_TYPES.map((type) => (
          <button
            key={type}
            onClick={() => onMediaTypeChange(type)}
            className={`text-sm font-black uppercase tracking-widest transition-all ${
              mediaType === type ? 'text-blue-500 scale-110' : 'text-gray-400 hover:text-white'
            }`}
          >
            {type}s
          </button>
        ))}
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-full">
          <Search className="w-4 h-4 text-gray-400" />
          <input
            type="search"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Rechercher…"
            aria-label="Rechercher"
            className="bg-transparent text-sm text-white placeholder-gray-500 outline-none w-40"
          />
        </div>
        <Link
          to="/explore/market/"
          className="flex items-center gap-3 px-6 py-2 bg-blue-400/10 border border-blue-400/20 rounded-full text-blue-500 font-black uppercase text-[10px] tracking-widest hover:bg-blue-400 hover:text-black transition-all group no-underline shadow-lg shadow-blue-400/5"
        >
          <Globe className="w-4 h-4 group-hover:rotate-12" /> Wiki Marché
        </Link>
        <Link
          to="/explore/seichijunrei/"
          className="flex items-center gap-3 px-6 py-2 bg-yellow-400/10 border border-yellow-400/20 rounded-full text-yellow-500 font-black uppercase text-[10px] tracking-widest hover:bg-yellow-400 hover:text-black transition-all group no-underline shadow-lg shadow-yellow-400/5"
        >
          <MapPin className="w-4 h-4 group-hover:animate-bounce" /> Carte Seichijunrei
        </Link>
      </div>
    </div>
    {genres.length > 0 && (
      <div className="flex flex-wrap gap-2">
        {genres.map((genre) => {
          const active = selectedGenres.has(genre);
          return (
            <button
              key={genre}
              onClick={() => onToggleGenre(genre)}
              className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest transition-all ${
                active ? 'bg-blue-500 text-white' : 'bg-white/5 text-gray-400 hover:text-white'
              }`}
            >
              {genre}
            </button>
          );
        })}
      </div>
    )}
  </div>
);
