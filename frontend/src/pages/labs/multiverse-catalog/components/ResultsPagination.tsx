import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { Pagination } from '../types';

interface ResultsPaginationProps {
  pagination: Pagination;
  onPrev: () => void;
  onNext: () => void;
  onSelectPage: (page: number) => void;
}

// ─── Pagination ──────────────────────────────────────────────────────
const ResultsPagination: React.FC<ResultsPaginationProps> = ({
  pagination,
  onPrev,
  onNext,
  onSelectPage,
}) => {
  return (
    <div className="mt-12 flex items-center justify-center gap-4">
      <button
        onClick={onPrev}
        disabled={!pagination.has_previous}
        className="flex cursor-pointer items-center gap-2 rounded-full border border-[#F4F1E8]/15 bg-transparent px-5 py-2.5 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:border-[#F4F1E8]/15 disabled:hover:text-[#8F94A5]"
      >
        <ChevronLeft className="h-3.5 w-3.5" /> Précédent
      </button>

      <div className="flex items-center gap-1">
        {Array.from({ length: Math.min(pagination.total_pages, 7) }, (_, i) => {
          let pageNum: number;
          const totalPages = pagination.total_pages;
          const currentPage = pagination.page;

          if (totalPages <= 7) {
            pageNum = i + 1;
          } else if (currentPage <= 4) {
            pageNum = i + 1;
          } else if (currentPage >= totalPages - 3) {
            pageNum = totalPages - 6 + i;
          } else {
            pageNum = currentPage - 3 + i;
          }

          return (
            <button
              key={pageNum}
              onClick={() => onSelectPage(pageNum)}
              className={`h-10 w-10 cursor-pointer rounded-xl text-[10px] font-black transition-colors ${
                pageNum === currentPage
                  ? 'border border-[#FDB913]/60 bg-[#FDB913]/10 text-[#FDB913]'
                  : 'border border-transparent bg-[#0F1016] text-[#8F94A5] hover:text-[#F4F1E8]'
              }`}
            >
              {pageNum}
            </button>
          );
        })}
      </div>

      <button
        onClick={onNext}
        disabled={!pagination.has_next}
        className="flex cursor-pointer items-center gap-2 rounded-full border border-[#F4F1E8]/15 bg-transparent px-5 py-2.5 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:border-[#F4F1E8]/15 disabled:hover:text-[#8F94A5]"
      >
        Suivant <ChevronRight className="h-3.5 w-3.5" />
      </button>
    </div>
  );
};

export default React.memo(ResultsPagination);
