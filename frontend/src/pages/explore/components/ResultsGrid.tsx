import React from 'react';
import { X } from 'lucide-react';
import { MediaCard, FeedItem } from './MediaCard';

interface ResultsGridProps {
  items: FeedItem[];
  onClear: () => void;
}

export const ResultsGrid: React.FC<ResultsGridProps> = ({ items, onClear }) => (
  <section className="space-y-6">
    <div className="flex items-center justify-between border-b border-white/5 pb-4">
      <h2 className="text-2xl font-black italic uppercase tracking-widest">
        {items.length} résultat{items.length > 1 ? 's' : ''}
      </h2>
      <button
        onClick={onClear}
        className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-full text-xs font-black uppercase tracking-widest text-gray-400 hover:text-white transition-all"
      >
        <X className="w-4 h-4" /> Effacer
      </button>
    </div>
    {items.length === 0 ? (
      <p className="py-24 text-center text-lg font-medium text-gray-400">Aucun résultat.</p>
    ) : (
      <div className="flex flex-wrap gap-6">
        {items.map((item) => (
          <MediaCard key={item.id} item={item} />
        ))}
      </div>
    )}
  </section>
);
