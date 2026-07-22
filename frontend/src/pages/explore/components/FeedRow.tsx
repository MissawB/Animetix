import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { MediaCard, FeedItem } from './MediaCard';

export type FeedRowData = {
  kind: string;
  title: string;
  reason: string;
  seed: { id: string; title: string } | null;
  items: FeedItem[];
};

export const RowHeader: React.FC<{ title: string; reason?: string }> = ({ title, reason }) => (
  <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
    <span className="h-6 w-1.5 flex-none bg-[#E8442B]" aria-hidden />
    <h2 className="font-manga text-xl font-black italic uppercase tracking-wide text-[#F4F1E8] md:text-2xl">
      {title}
    </h2>
    {reason && (
      <span className="text-xs font-semibold uppercase italic tracking-widest text-[#E8442B]">
        {reason}
      </span>
    )}
    <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
  </div>
);

export const FeedRow: React.FC<{ row: FeedRowData; rowId: string }> = ({ row, rowId }) => {
  const scrollBy = (dx: number) => {
    const el = document.getElementById(rowId);
    if (el) el.scrollBy({ left: dx, behavior: 'smooth' });
  };

  if (!row.items?.length) return null;

  return (
    <div className="space-y-4">
      <RowHeader title={row.title} reason={row.reason} />
      <div className="relative group/row">
        <button
          type="button"
          onClick={() => scrollBy(-400)}
          aria-label="Défiler à gauche"
          className="absolute left-0 top-0 bottom-0 w-12 z-30 bg-gradient-to-r from-[#0B0C10] to-transparent text-[#F4F1E8] opacity-0 group-hover/row:opacity-100 focus-visible:opacity-100 transition-opacity flex items-center justify-center"
        >
          <ChevronLeft size={32} />
        </button>
        <div id={rowId} className="flex gap-6 overflow-x-auto no-scrollbar pb-4">
          {row.items.map((item) => (
            <MediaCard key={item.id} item={item} />
          ))}
        </div>
        <button
          type="button"
          onClick={() => scrollBy(400)}
          aria-label="Défiler à droite"
          className="absolute right-0 top-0 bottom-0 w-12 z-30 bg-gradient-to-l from-[#0B0C10] to-transparent text-[#F4F1E8] opacity-0 group-hover/row:opacity-100 focus-visible:opacity-100 transition-opacity flex items-center justify-center"
        >
          <ChevronRight size={32} />
        </button>
      </div>
    </div>
  );
};
