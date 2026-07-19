import React from 'react';
import { Link } from 'react-router-dom';
import type { RelatedItem } from '../../../types';

interface RelatedCarouselProps {
  items: RelatedItem[];
  mediaType: string;
}

export const RelatedCarousel: React.FC<RelatedCarouselProps> = ({ items, mediaType }) => (
  <div className="flex gap-6 overflow-x-auto no-scrollbar pb-4">
    {items.map((rel) => (
      <Link
        key={rel.id}
        to={`/media/${mediaType}/${rel.id}/`}
        className="no-underline group flex-none w-40 md:w-44"
      >
        <div className="aspect-[2/3] rounded-xl overflow-hidden bg-gray-900 mb-3 border border-white/5 group-hover:border-purple-500/30 transition-all group-hover:scale-105 shadow-xl">
          <img
            src={rel.image}
            className="w-full h-full object-cover"
            alt={rel.title}
            loading="lazy"
            decoding="async"
          />
        </div>
        <p className="text-[10px] font-black uppercase tracking-tighter line-clamp-1 opacity-50 group-hover:text-purple-400 group-hover:opacity-100 transition-all">
          {rel.title}
        </p>
      </Link>
    ))}
  </div>
);
