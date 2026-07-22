import React from 'react';
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { motion, MotionConfig } from 'framer-motion';
import { Link } from 'react-router-dom';

import { apiClient } from '../../utils/apiClient';
import { FeedRow, FeedRowData, RowHeader } from './components/FeedRow';
import { HeroBanner } from './components/HeroBanner';
import { ExploreToolbar } from './components/ExploreToolbar';
import { ResultsGrid } from './components/ResultsGrid';
import { FeedSkeleton, ErrorState, EmptyState } from './components/FeedStates';
import { useExploreFilter } from './hooks/useExploreFilter';

interface ExploreFeed {
  rows: FeedRowData[];
  personalized: boolean;
}

const ExplorePage: React.FC = () => {
  const [mediaType, setMediaType] = React.useState('Anime');
  const [query, setQuery] = React.useState('');
  const [selectedGenres, setSelectedGenres] = React.useState<Set<string>>(new Set());

  const { data, isLoading, isError, refetch } = useQuery<ExploreFeed>({
    queryKey: ['explore', mediaType],
    queryFn: () => apiClient(`/api/v1/explore/?media_type=${mediaType}`),
    placeholderData: keepPreviousData,
  });

  const rows = data?.rows ?? [];
  const { derivedGenres, results } = useExploreFilter(rows, query, selectedGenres);

  const isFiltering = query.trim() !== '' || selectedGenres.size > 0;

  const heroRowIndex = rows.findIndex((r) => r.items.length > 0);
  const hero = heroRowIndex >= 0 ? rows[heroRowIndex].items[0] : undefined;

  const changeMediaType = (type: string) => {
    setMediaType(type);
    setSelectedGenres(new Set());
  };

  const toggleGenre = (genre: string) => {
    setSelectedGenres((prev) => {
      const next = new Set(prev);
      if (next.has(genre)) next.delete(genre);
      else next.add(genre);
      return next;
    });
  };

  const clearFilters = () => {
    setQuery('');
    setSelectedGenres(new Set());
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        <FeedSkeleton />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        <ErrorState onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
        {hero && <HeroBanner hero={hero} mediaType={mediaType} />}

        <div className="relative z-20 space-y-14 px-4 pb-24 sm:px-8 lg:px-12">
          <ExploreToolbar
            mediaType={mediaType}
            onMediaTypeChange={changeMediaType}
            query={query}
            onQueryChange={setQuery}
            genres={derivedGenres}
            selectedGenres={selectedGenres}
            onToggleGenre={toggleGenre}
          />

          {data && !data.personalized && !isFiltering && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="relative overflow-hidden rounded-2xl border border-[#E8442B]/40 bg-gradient-to-r from-[#E8442B]/[0.10] via-[#E8442B]/[0.04] to-transparent"
            >
              <span className="explore-halftone absolute inset-0 opacity-60" aria-hidden />
              <span className="absolute inset-y-0 left-0 w-1 bg-[#E8442B]" aria-hidden />
              <div className="relative flex flex-wrap items-center gap-x-6 gap-y-4 px-6 py-6 sm:px-8">
                <div className="min-w-[220px] flex-1">
                  <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                    Édition personnalisée
                  </p>
                  <p className="font-manga mt-1 text-lg font-black uppercase italic tracking-wide text-[#F4F1E8]">
                    Personnalise ton feed
                  </p>
                  <p className="mt-1 max-w-xl text-sm leading-relaxed text-[#8F94A5]">
                    Connecte-toi et ajoute des favoris pour que l'IA affine tes recommandations.
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <Link
                    to="/auth/login/"
                    className="rounded-full bg-[#FDB913] px-6 py-2.5 text-xs font-black uppercase tracking-widest text-[#0B0C10] no-underline transition-transform hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                  >
                    Se connecter
                  </Link>
                  <Link
                    to="/auth/register/"
                    className="rounded-full border border-[#F4F1E8]/20 px-6 py-2.5 text-xs font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:border-[#F4F1E8]/50 hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                  >
                    Créer un compte
                  </Link>
                </div>
              </div>
            </motion.div>
          )}

          {isFiltering ? (
            <ResultsGrid items={results} onClear={clearFilters} />
          ) : rows.length === 0 || rows.every((r) => r.items.length === 0) ? (
            <EmptyState />
          ) : (
            <section className="space-y-12">
              {rows.map((row, idx) => {
                if (idx === heroRowIndex) {
                  const remainingItems = row.items.slice(1);
                  if (remainingItems.length === 0) {
                    return (
                      <div key={`${row.kind}-${idx}`} className="space-y-4">
                        <RowHeader title={row.title} reason={row.reason} />
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
          )}
        </div>

        <style>{`
          .no-scrollbar::-webkit-scrollbar { display: none; }
          .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
          .explore-halftone {
            background-image: radial-gradient(rgba(244, 241, 232, 0.14) 1px, transparent 1.4px);
            background-size: 14px 14px;
            -webkit-mask-image: radial-gradient(ellipse at 72% 35%, black 0%, transparent 68%);
            mask-image: radial-gradient(ellipse at 72% 35%, black 0%, transparent 68%);
          }
          .explore-stamp {
            display: inline-block;
            border: 2px solid #E8442B;
            border-radius: 2px;
            color: #E8442B;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.1em;
            padding: 2px 6px;
          }
          .explore-vertical { writing-mode: vertical-rl; }
        `}</style>
      </div>
    </MotionConfig>
  );
};

export default ExplorePage;
