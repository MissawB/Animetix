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

export const FeedRow: React.FC<{ row: FeedRowData; rowId: string }> = ({ row, rowId }) => {
  const scrollBy = (dx: number) => {
    const el = document.getElementById(rowId);
    if (el) el.scrollBy({ left: dx, behavior: 'smooth' });
  };

  if (!row.items?.length) return null;

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-black italic uppercase tracking-widest flex items-center gap-3">
        {row.title}
        {row.reason && (
          <span className="text-xs bg-blue-500 text-white px-2 py-1 rounded font-normal not-italic ml-2">
            {row.reason}
          </span>
        )}
        <span className="h-px bg-blue-500/30 flex-1" />
      </h2>
      <div className="relative group/row">
        <button
          onClick={() => scrollBy(-400)}
          aria-label="Défiler à gauche"
          className="absolute left-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover/row:opacity-100 transition-opacity flex items-center justify-center"
        >
          <ChevronLeft size={32} />
        </button>
        <div id={rowId} className="flex gap-6 overflow-x-auto no-scrollbar pb-4">
          {row.items.map((item) => (
            <MediaCard key={item.id} item={item} />
          ))}
        </div>
        <button
          onClick={() => scrollBy(400)}
          aria-label="Défiler à droite"
          className="absolute right-0 top-0 bottom-0 w-12 z-30 bg-black/50 opacity-0 group-hover/row:opacity-100 transition-opacity flex items-center justify-center"
        >
          <ChevronRight size={32} />
        </button>
      </div>
    </div>
  );
};
