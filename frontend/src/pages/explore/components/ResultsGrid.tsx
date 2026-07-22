import React from 'react';
import { X } from 'lucide-react';
import { MediaCard, FeedItem } from './MediaCard';

interface ResultsGridProps {
  items: FeedItem[];
  onClear: () => void;
}

export const ResultsGrid: React.FC<ResultsGridProps> = ({ items, onClear }) => (
  <section className="space-y-6">
    <div className="flex items-center justify-between border-b border-[#F4F1E8]/10 pb-4">
      <div className="flex items-center gap-4">
        <span className="h-6 w-1.5 flex-none bg-[#E8442B]" aria-hidden />
        <h2 className="font-manga text-xl font-black uppercase italic tracking-wide text-[#F4F1E8] md:text-2xl">
          {items.length} résultat{items.length > 1 ? 's' : ''}
        </h2>
      </div>
      <button
        type="button"
        onClick={onClear}
        className="flex items-center gap-2 rounded-sm border border-[#F4F1E8]/15 px-4 py-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#F4F1E8]/40 hover:text-[#F4F1E8] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
      >
        <X className="h-4 w-4" /> Effacer
      </button>
    </div>
    {items.length === 0 ? (
      <p className="py-24 text-center text-lg font-medium text-[#8F94A5]">Aucun résultat.</p>
    ) : (
      <div className="flex flex-wrap gap-6">
        {items.map((item) => (
          <MediaCard key={item.id} item={item} />
        ))}
      </div>
    )}
  </section>
);
