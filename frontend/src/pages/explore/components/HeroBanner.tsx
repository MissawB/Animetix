import React from 'react';
import { motion } from 'framer-motion';
import { Info, Star } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { FeedItem } from './MediaCard';

export const HeroBanner: React.FC<{ hero: FeedItem; mediaType: string }> = ({
  hero,
  mediaType,
}) => (
  <section className="relative w-full overflow-hidden border-b border-[#F4F1E8]/10">
    {hero.image && (
      <img
        src={hero.image}
        alt=""
        aria-hidden
        className="absolute inset-0 h-full w-full scale-110 object-cover opacity-20 blur-2xl"
        loading="lazy"
        decoding="async"
      />
    )}
    <div className="absolute inset-0 bg-gradient-to-b from-[#0B0C10]/70 via-[#0B0C10]/85 to-[#0B0C10]" />
    <div className="explore-halftone absolute inset-0" aria-hidden />

    <div className="relative z-10 mx-auto flex min-h-[62vh] max-w-7xl flex-col items-start gap-10 px-4 py-14 sm:px-8 lg:flex-row lg:items-end lg:justify-between lg:px-12 lg:py-20">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="max-w-2xl space-y-5"
      >
        <div className="flex items-center gap-3">
          <span className="explore-stamp -rotate-2" aria-hidden>
            特集
          </span>
          <span className="text-xs font-black uppercase tracking-[0.3em] text-[#E8442B]">
            À la une · {mediaType}
          </span>
        </div>
        <h1 className="font-manga text-5xl font-black italic uppercase leading-[0.9] tracking-tighter text-[#F4F1E8] md:text-7xl xl:text-8xl">
          {hero.title}
        </h1>
        <div className="flex flex-wrap items-center gap-4 text-sm font-bold uppercase tracking-widest">
          {hero.rating != null && (
            <span className="flex items-center gap-1 text-[#FDB913]">
              <Star size={14} fill="currentColor" /> {hero.rating.toFixed(1)}
            </span>
          )}
          {hero.year != null && <span className="text-[#F4F1E8]/80">{hero.year}</span>}
          {(hero.genres ?? []).slice(0, 3).map((genre) => (
            <span key={genre} className="text-[#8F94A5]">
              {genre}
            </span>
          ))}
        </div>
        {hero.synopsis_fr && (
          <p className="line-clamp-3 text-lg font-medium leading-relaxed text-[#8F94A5]">
            {hero.synopsis_fr}
          </p>
        )}
        <Link
          to={`/media/${hero.media_type}/${hero.id}/`}
          className="inline-flex items-center gap-2 rounded-sm bg-[#E8442B] px-8 py-4 font-manga font-black uppercase italic text-[#F4F1E8] no-underline transition-transform hover:-translate-y-0.5 hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
        >
          <Info size={20} /> Voir la fiche
        </Link>
      </motion.div>

      {hero.image && (
        <motion.div
          initial={{ opacity: 0, rotate: 6, y: 30 }}
          animate={{ opacity: 1, rotate: 2, y: 0 }}
          whileHover={{ rotate: 3, y: -8 }}
          transition={{ duration: 0.6, ease: 'easeOut', delay: 0.15 }}
          className="relative hidden flex-none self-center lg:block"
        >
          <Link
            to={`/media/${hero.media_type}/${hero.id}/`}
            aria-label={`Voir la fiche de ${hero.title}`}
            className="group relative block rounded-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#FDB913]"
          >
            <span
              className="absolute -inset-2 translate-x-4 translate-y-4 rounded-sm border-2 border-[#E8442B]/60 transition-transform duration-300 group-hover:translate-x-6 group-hover:translate-y-6"
              aria-hidden
            />
            <img
              src={hero.image}
              alt=""
              className="relative aspect-[2/3] w-56 rounded-sm object-cover shadow-[0_24px_60px_-12px_rgba(0,0,0,0.8)] ring-1 ring-[#F4F1E8]/15 transition-all duration-300 group-hover:shadow-[0_36px_80px_-12px_rgba(0,0,0,0.9)] group-hover:ring-2 group-hover:ring-[#FDB913]/70 xl:w-64"
              loading="lazy"
              decoding="async"
            />
            <span
              className="explore-vertical absolute -right-12 top-0 text-xs tracking-[0.35em] text-[#F4F1E8]/50 transition-colors duration-300 group-hover:text-[#FDB913]/80"
              aria-hidden
            >
              今週の一押し
            </span>
          </Link>
        </motion.div>
      )}
    </div>
  </section>
);
