import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { TrendingUp, Info, MapPin, Globe, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

import { apiClient } from '../../utils/apiClient';
import { FeedRow, FeedRowData } from './components/FeedRow';

interface ExploreFeed {
  rows: FeedRowData[];
  personalized: boolean;
}

const ExplorePage: React.FC = () => {
  const [mediaType, setMediaType] = React.useState('Anime');

  const { data } = useQuery<ExploreFeed>({
    queryKey: ['explore', mediaType],
    queryFn: () => apiClient(`/api/v1/explore/?media_type=${mediaType}`),
  });

  const rows = data?.rows ?? [];
  const heroRowIndex = rows.findIndex((r) => r.items.length > 0);
  const hero = heroRowIndex >= 0 ? rows[heroRowIndex].items[0] : undefined;

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Hero */}
      <section className="relative h-[70vh] w-full overflow-hidden">
        {hero && (
          <>
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
          </>
        )}
      </section>

      <div className="px-12 -mt-12 relative z-20 space-y-16 pb-24">
        {/* Sélecteur + liens */}
        <div className="flex justify-between items-center border-b border-white/5 pb-4">
          <div className="flex gap-6">
            {['Anime', 'Manga', 'Game', 'Movie'].map((type) => (
              <button
                key={type}
                onClick={() => setMediaType(type)}
                className={`text-sm font-black uppercase tracking-widest transition-all ${
                  mediaType === type ? 'text-blue-500 scale-110' : 'text-gray-400 hover:text-white'
                }`}
              >
                {type}s
              </button>
            ))}
          </div>
          <div className="flex gap-4">
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

        {/* Bandeau cold-start */}
        {data && !data.personalized && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-4 rounded-2xl border border-blue-500/20 bg-blue-500/5 px-6 py-5"
          >
            <Sparkles className="w-8 h-8 text-blue-400 flex-none" />
            <div>
              <p className="font-black uppercase italic tracking-widest">Personnalise ton feed</p>
              <p className="text-sm text-gray-400">
                Connecte-toi et ajoute des favoris pour que l'IA affine tes recommandations.
              </p>
            </div>
          </motion.div>
        )}

        {/* Rangées du feed */}
        <section className="space-y-12">
          {rows.map((row, idx) => {
            // La rangée qui fournit le héros n'affiche pas une seconde fois ce même item
            // (déjà mis en avant en haut de page).
            if (idx === heroRowIndex) {
              const remainingItems = row.items.slice(1);
              if (remainingItems.length === 0) {
                return (
                  <div key={`${row.kind}-${idx}`} className="space-y-4">
                    <h2 className="text-2xl font-black italic uppercase tracking-widest flex items-center gap-3">
                      {row.title}
                      {row.reason && (
                        <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded font-normal not-italic ml-2">
                          {row.reason}
                        </span>
                      )}
                      <span className="h-px bg-blue-500/30 flex-1" />
                    </h2>
                  </div>
                );
              }
              return (
                <FeedRow
                  key={`${row.kind}-${idx}`}
                  row={{ ...row, items: remainingItems }}
                  rowId={`feed-row-${idx}`}
                />
              );
            }
            return <FeedRow key={`${row.kind}-${idx}`} row={row} rowId={`feed-row-${idx}`} />;
          })}
        </section>
      </div>

      <style>{`
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
    </div>
  );
};

export default ExplorePage;
