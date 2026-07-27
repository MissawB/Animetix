import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react';

interface CatalogPaginationProps {
  page: number;
  hasNextPage: boolean;
  lastPage: number | null;
  onGoToPage: (n: number) => void;
  onSeekLetter: (letter: string) => void;
}

const LETTERS = ['#', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('')];

const navBtn =
  'inline-flex items-center gap-1.5 rounded-lg border border-[#F4F1E8]/15 px-3 py-2 text-sm font-bold text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:border-[#F4F1E8]/15 disabled:hover:text-[#8F94A5]';

const CatalogPaginationComponent: React.FC<CatalogPaginationProps> = ({
  page,
  hasNextPage,
  lastPage,
  onGoToPage,
  onSeekLetter,
}) => {
  const [jumpValue, setJumpValue] = useState('');

  const handleJump = (e: React.FormEvent) => {
    e.preventDefault();
    const n = parseInt(jumpValue, 10);
    if (Number.isNaN(n) || n < 1) return;
    onGoToPage(lastPage ? Math.min(n, lastPage) : n);
    setJumpValue('');
  };

  const canLast = lastPage != null && page < lastPage;

  return (
    <div className="space-y-4 pt-2">
      {/* Navigation alphabétique */}
      <div className="flex flex-wrap items-center justify-center gap-1.5">
        <span className="mr-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
          A→Z
        </span>
        {LETTERS.map((letter) => (
          <button
            key={letter}
            type="button"
            onClick={() => onSeekLetter(letter)}
            title={`Aller à « ${letter} »`}
            className="h-7 w-7 rounded-md border border-[#F4F1E8]/10 text-xs font-black tabular-nums text-[#8F94A5] transition-colors hover:border-[#E8442B] hover:text-[#F4F1E8]"
          >
            {letter}
          </button>
        ))}
      </div>

      {/* Pagination numérique */}
      <nav
        aria-label="Pagination du catalogue"
        className="flex flex-wrap items-center justify-center gap-3"
      >
        <button
          type="button"
          onClick={() => onGoToPage(1)}
          disabled={page <= 1}
          title="Première page"
          aria-label="Première page"
          className={navBtn}
        >
          <ChevronsLeft className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => onGoToPage(page - 1)}
          disabled={page <= 1}
          className={navBtn}
        >
          <ChevronLeft className="h-4 w-4" /> Préc.
        </button>

        <form onSubmit={handleJump} className="flex items-center gap-2">
          <span className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">Page</span>
          <input
            type="number"
            min={1}
            max={lastPage ?? undefined}
            value={jumpValue}
            onChange={(e) => setJumpValue(e.target.value)}
            placeholder={String(page)}
            aria-label="Aller à la page"
            className="w-16 rounded-md border border-[#F4F1E8]/15 bg-[#0B0C10] px-2 py-2 text-center text-sm font-bold tabular-nums text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
          />
          {lastPage != null && (
            <span className="text-sm font-bold tabular-nums text-[#8F94A5]">/ {lastPage}</span>
          )}
          <button
            type="submit"
            className="rounded-lg border border-[#F4F1E8]/15 px-3 py-2 text-xs font-black uppercase tracking-wide text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]"
          >
            Aller
          </button>
        </form>

        <button
          type="button"
          onClick={() => onGoToPage(page + 1)}
          disabled={!hasNextPage}
          className={navBtn}
        >
          Suiv. <ChevronRight className="h-4 w-4" />
        </button>
        <button
          type="button"
          onClick={() => lastPage != null && onGoToPage(lastPage)}
          disabled={!canLast}
          title="Dernière page"
          aria-label="Dernière page"
          className={navBtn}
        >
          <ChevronsRight className="h-4 w-4" />
        </button>
      </nav>
    </div>
  );
};

export const CatalogPagination = React.memo(CatalogPaginationComponent);
