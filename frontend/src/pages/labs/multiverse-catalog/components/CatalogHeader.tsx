import React from 'react';

// ─── Hero Header (plaque de protocole, style LabKit) ─────────────────
const CatalogHeader: React.FC<{ total: number | undefined }> = ({ total }) => {
  return (
    <header className="relative border-b border-[#F4F1E8]/10">
      <div className="relative mx-auto max-w-7xl px-4 py-12 sm:px-6">
        <div
          className="explore-halftone pointer-events-none absolute -top-4 inset-x-0 h-40"
          aria-hidden
        />
        <div className="relative flex flex-col justify-between gap-8 md:flex-row md:items-end">
          <div>
            <div className="flex items-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                実験
              </span>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                Catalogue · Multiverse
              </span>
            </div>
            <h1 className="font-manga mt-4 text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-6xl">
              Multiverse <span className="text-[#E8442B]">Gallery</span>
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#8F94A5]">
              Explorez les univers synthétiques générés par l'intelligence artificielle.
            </p>
          </div>

          <div className="text-left md:text-right">
            <p className="text-[9px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
              Univers total
            </p>
            <p className="font-manga mt-2 text-4xl font-black italic leading-none text-[#FDB913]">
              {total ?? '—'}
            </p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default React.memo(CatalogHeader);
