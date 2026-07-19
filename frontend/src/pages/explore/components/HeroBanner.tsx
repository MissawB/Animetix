import React from 'react';
import { TrendingUp, Info, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { FeedItem } from './MediaCard';

export const HeroBanner: React.FC<{ hero: FeedItem; mediaType: string }> = ({
  hero,
  mediaType,
}) => (
  <section className="relative h-[70vh] w-full overflow-hidden">
    <img
      src={hero.image}
      className="absolute inset-0 w-full h-full object-cover opacity-40 blur-sm scale-105"
      alt="Hero Background"
      loading="lazy"
      decoding="async"
    />
    <div className="absolute inset-0 bg-gradient-to-t from-[#0a0a0a] via-transparent to-transparent" />
    <div className="absolute bottom-20 left-12 max-w-2xl space-y-6">
      <div className="flex items-center gap-2 text-yellow-500 font-black uppercase tracking-widest text-xs">
        <TrendingUp size={16} /> À la une {mediaType}
      </div>
      <div className="flex items-center gap-4 text-sm font-black uppercase tracking-widest">
        {hero.rating != null && (
          <span className="flex items-center gap-1 text-yellow-400">
            <Star size={14} fill="currentColor" /> {hero.rating.toFixed(1)}
          </span>
        )}
        {hero.year != null && <span className="text-gray-300">{hero.year}</span>}
        {(hero.genres ?? []).slice(0, 3).map((genre) => (
          <span key={genre} className="text-gray-400">
            {genre}
          </span>
        ))}
      </div>
      <h1 className="text-6xl md:text-8xl font-black italic uppercase tracking-tighter leading-none">
        {hero.title}
      </h1>
      {hero.synopsis_fr && (
        <p className="text-gray-400 text-lg line-clamp-3 font-medium leading-relaxed">
          {hero.synopsis_fr}
        </p>
      )}
      <Link
        to={`/media/${hero.media_type.toLowerCase()}/${hero.id}/`}
        className="inline-flex px-8 py-4 bg-white text-black font-black uppercase italic rounded-xl items-center gap-2 hover:bg-gray-200 transition-all hover:scale-105 no-underline"
      >
        <Info size={20} /> Voir la fiche
      </Link>
    </div>
  </section>
);
