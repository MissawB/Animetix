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
const ResultsPagination: React.FC<ResultsPaginationProps> = ({ pagination, onPrev, onNext, onSelectPage }) => {
  return (
    <div className="flex items-center justify-center gap-4 mt-12">
      <button
        onClick={onPrev}
        disabled={!pagination.has_previous}
        className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest disabled:opacity-20 hover:bg-white/10 transition-all"
      >
        <ChevronLeft className="w-3.5 h-3.5" /> Précédent
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
              className={`w-10 h-10 rounded-xl text-[10px] font-black transition-all ${
                pageNum === currentPage
                  ? 'bg-cyan-500/20 border border-cyan-500/30 text-cyan-400'
                  : 'bg-white/[0.02] hover:bg-white/5 opacity-40 hover:opacity-100'
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
        className="flex items-center gap-2 px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest disabled:opacity-20 hover:bg-white/10 transition-all"
      >
        Suivant <ChevronRight className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};

export default React.memo(ResultsPagination);
