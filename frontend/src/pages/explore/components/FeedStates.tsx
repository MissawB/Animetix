import React from 'react';

export const FeedSkeleton: React.FC = () => (
  <div data-testid="feed-skeleton" className="animate-pulse">
    <div className="mx-auto flex min-h-[62vh] max-w-7xl items-end justify-between gap-10 border-b border-white/5 px-4 py-14 sm:px-8 lg:px-12 lg:py-20">
      <div className="max-w-2xl flex-1 space-y-5">
        <div className="h-4 w-44 rounded bg-white/10" />
        <div className="h-20 w-full max-w-xl rounded bg-white/10" />
        <div className="h-4 w-72 rounded bg-white/5" />
        <div className="h-4 w-96 max-w-full rounded bg-white/5" />
        <div className="h-12 w-44 rounded-sm bg-white/10" />
      </div>
      <div className="hidden aspect-[2/3] w-56 rotate-2 rounded-sm bg-white/5 lg:block" />
    </div>
    <div className="mt-10 space-y-12 px-4 sm:px-8 lg:px-12">
      {Array.from({ length: 3 }).map((_, rowIdx) => (
        <div key={rowIdx} className="space-y-4">
          <div className="h-6 w-64 rounded bg-white/10" />
          <div className="flex gap-6 overflow-hidden">
            {Array.from({ length: 6 }).map((_, cardIdx) => (
              <div
                key={cardIdx}
                className="aspect-[2/3] w-48 flex-none rounded-[4px] bg-white/5 md:w-56"
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
    <p className="font-manga text-lg font-black uppercase italic tracking-widest text-[#F4F1E8]">
      Impossible de charger le feed
    </p>
    <p className="text-sm text-[#8F94A5]">Vérifie ta connexion, puis relance l'édition.</p>
    <button
      type="button"
      onClick={onRetry}
      className="rounded-sm bg-[#E8442B] px-6 py-3 font-manga font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
    >
      Réessayer
    </button>
  </div>
);

export const EmptyState: React.FC<{ message?: string }> = ({
  message = 'Aucune reco pour ce type pour le moment.',
}) => (
  <div className="flex items-center justify-center py-32 text-center">
    <p className="text-lg font-medium text-[#8F94A5]">{message}</p>
  </div>
);
