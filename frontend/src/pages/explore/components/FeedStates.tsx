import React from 'react';

export const FeedSkeleton: React.FC = () => (
  <div data-testid="feed-skeleton" className="animate-pulse">
    <div className="h-[70vh] w-full bg-white/5" />
    <div className="px-12 mt-8 space-y-12">
      {Array.from({ length: 3 }).map((_, rowIdx) => (
        <div key={rowIdx} className="space-y-4">
          <div className="h-6 w-64 bg-white/10 rounded" />
          <div className="flex gap-6">
            {Array.from({ length: 6 }).map((_, cardIdx) => (
              <div
                key={cardIdx}
                className="flex-none w-48 md:w-56 aspect-[2/3] rounded-xl bg-white/5"
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  </div>
);

export const ErrorState: React.FC<{ onRetry: () => void }> = ({ onRetry }) => (
  <div className="flex flex-col items-center justify-center gap-4 py-32 text-center">
    <p className="text-lg font-black uppercase italic tracking-widest text-gray-300">
      Impossible de charger le feed
    </p>
    <button
      onClick={onRetry}
      className="px-6 py-3 bg-white text-black font-black uppercase italic rounded-xl hover:bg-gray-200 transition-all"
    >
      Réessayer
    </button>
  </div>
);

export const EmptyState: React.FC<{ message?: string }> = ({
  message = 'Aucune reco pour ce type pour le moment.',
}) => (
  <div className="flex items-center justify-center py-32 text-center">
    <p className="text-lg font-medium text-gray-400">{message}</p>
  </div>
);
