import React from 'react';
import { Sparkles } from 'lucide-react';

// ─── Hero Header ─────────────────────────────────────────────────────
const CatalogHeader: React.FC<{ total: number | undefined }> = ({ total }) => {
  return (
    <header className="relative overflow-hidden border-b border-white/5">
      {/* Background decor */}
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-950/20 via-transparent to-purple-950/10" />
      <div className="absolute top-10 right-20 w-64 h-64 bg-cyan-500/5 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-20 w-48 h-48 bg-purple-500/5 rounded-full blur-3xl" />

      <div className="max-w-7xl mx-auto px-6 py-16 relative z-10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-[10px] font-black uppercase tracking-widest text-cyan-500 mb-4">
              <Sparkles className="w-3 h-3" /> Catalogue Communautaire
            </div>
            <h1 className="text-6xl md:text-7xl font-black italic manga-font tracking-tighter uppercase mb-2">
              MULTIVERSE <span className="text-cyan-500 text-glow">GALLERY</span>
            </h1>
            <p className="text-lg font-bold opacity-30 uppercase tracking-[0.2em] leading-relaxed">
              Explorez les univers synthétiques générés par l'intelligence artificielle
            </p>
          </div>

          <div className="flex flex-col items-end gap-2">
            <div className="text-right">
              <p className="text-[10px] font-black uppercase opacity-25 mb-1">Univers Total</p>
              <p className="text-4xl font-black italic manga-font text-cyan-400">
                {total ?? '—'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default React.memo(CatalogHeader);
