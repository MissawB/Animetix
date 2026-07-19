import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

import { apiClient } from '../../utils/apiClient';
import { FeedRow, FeedRowData } from './components/FeedRow';
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
  });

  const rows = data?.rows ?? [];
  const { derivedGenres, results } = useExploreFilter(rows, query, selectedGenres);

  const isFiltering = query.trim() !== '' || selectedGenres.size > 0;

  const heroRowIndex = rows.findIndex((r) => r.items.length > 0);
  const hero = heroRowIndex >= 0 ? rows[heroRowIndex].items[0] : undefined;

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
      <div className="min-h-screen bg-[#0a0a0a] text-white">
        <FeedSkeleton />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-[#0a0a0a] text-white">
        <ErrorState onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {hero && <HeroBanner hero={hero} mediaType={mediaType} />}

      <div className="px-12 -mt-12 relative z-20 space-y-16 pb-24">
        <ExploreToolbar
          mediaType={mediaType}
          onMediaTypeChange={setMediaType}
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

        {isFiltering ? (
          <ResultsGrid items={results} onClear={clearFilters} />
        ) : rows.length === 0 ? (
          <EmptyState />
        ) : (
          <section className="space-y-12">
            {rows.map((row, idx) => {
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
        )}
      </div>

      <style>{`
        .no-scrollbar::-webkit-scrollbar { display: none; }
        .no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
    </div>
  );
};

export default ExplorePage;
