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
        className="group w-40 flex-none no-underline md:w-44 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#FDB913]"
      >
        <div className="mb-3 aspect-[2/3] overflow-hidden rounded-[4px] bg-[#F4F1E8]/5 ring-1 ring-[#F4F1E8]/10 transition-all group-hover:-translate-y-1 group-hover:ring-[#FDB913]/60">
          <img
            src={rel.image}
            className="h-full w-full object-cover"
            alt={rel.title}
            loading="lazy"
            decoding="async"
          />
        </div>
        <p className="line-clamp-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors group-hover:text-[#F4F1E8]">
          {rel.title}
        </p>
      </Link>
    ))}
  </div>
);
