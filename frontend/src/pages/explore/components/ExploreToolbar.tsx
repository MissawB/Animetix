import React from 'react';
import { Globe, MapPin, Search } from 'lucide-react';
import { Link } from 'react-router-dom';

const MEDIA_TYPES: Array<{ key: string; jp: string }> = [
  { key: 'Anime', jp: 'アニメ' },
  { key: 'Manga', jp: 'マンガ' },
  { key: 'Game', jp: 'ゲーム' },
  { key: 'Movie', jp: '映画' },
];

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
  <div className="z-30 space-y-4 border-b border-[#F4F1E8]/10 bg-[#0B0C10]/90 py-4 backdrop-blur lg:sticky lg:top-0">
    <div className="flex flex-wrap items-center justify-between gap-4">
      <div className="flex gap-6">
        {MEDIA_TYPES.map(({ key, jp }) => {
          const active = mediaType === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => onMediaTypeChange(key)}
              className="group relative pb-1 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#FDB913]"
            >
              <span
                className={`font-manga block text-sm font-black uppercase italic tracking-widest transition-colors ${
                  active ? 'text-[#F4F1E8]' : 'text-[#8F94A5] group-hover:text-[#F4F1E8]'
                }`}
              >
                {key}s
              </span>
              <span
                aria-hidden
                className={`block text-[9px] tracking-[0.4em] transition-colors ${
                  active ? 'text-[#E8442B]' : 'text-[#8F94A5]/50'
                }`}
              >
                {jp}
              </span>
              <span
                aria-hidden
                className={`absolute -bottom-1 left-0 h-[3px] bg-[#E8442B] transition-all ${
                  active ? 'w-full' : 'w-0'
                }`}
              />
            </button>
          );
        })}
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2 border-b border-[#F4F1E8]/20 px-1 py-2 transition-colors focus-within:border-[#FDB913]">
          <Search className="h-4 w-4 text-[#8F94A5]" />
          <input
            type="search"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Rechercher…"
            aria-label="Rechercher"
            className="w-40 bg-transparent text-sm text-[#F4F1E8] outline-none placeholder:text-[#8F94A5]/70"
          />
        </div>
        <Link
          to="/explore/market/"
          className="flex items-center gap-2 rounded-sm border border-[#F4F1E8]/15 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:border-[#E8442B] hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
        >
          <Globe className="h-4 w-4" /> Wiki Marché
        </Link>
        <Link
          to="/explore/seichijunrei/"
          className="flex items-center gap-2 rounded-sm border border-[#F4F1E8]/15 px-4 py-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
        >
          <MapPin className="h-4 w-4" /> Carte Seichijunrei
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
              type="button"
              onClick={() => onToggleGenre(genre)}
              className={`rounded-sm px-3 py-1 text-[10px] font-black uppercase tracking-widest transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] ${
                active
                  ? 'bg-[#FDB913] text-[#0B0C10]'
                  : 'border border-[#F4F1E8]/15 text-[#8F94A5] hover:border-[#F4F1E8]/40 hover:text-[#F4F1E8]'
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
