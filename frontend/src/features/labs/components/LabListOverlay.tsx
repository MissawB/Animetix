import React from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowRight } from 'lucide-react';

export interface OverlayCategory {
  id: string;
  /** Titre traduit de la catégorie. */
  title: string;
  /** Kanji de la catégorie. */
  glyph: string;
  /** Couleur de la catégorie (hex). */
  hex: string;
}

export interface OverlayLab {
  id: string;
  title: string;
  url: string;
  desc: string;
  glyph?: string;
}

interface LabListOverlayProps {
  categories: OverlayCategory[];
  /** Catégorie ouverte (null = fermé). */
  selected: string | null;
  labs: OverlayLab[];
  onSelect: (id: string) => void;
  onClose: () => void;
}

/** Menu des ateliers d'une catégorie : dialogue plein écran avec onglets de
 *  catégories (navigation sans fermer), sceaux kanji et accents à la couleur
 *  de la catégorie active. Échap ferme. */
export const LabListOverlay: React.FC<LabListOverlayProps> = ({
  categories,
  selected,
  labs,
  onSelect,
  onClose,
}) => {
  const active = categories.find((c) => c.id === selected);

  React.useEffect(() => {
    if (!selected) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [selected, onClose]);

  return (
    <AnimatePresence>
      {selected && active && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          role="dialog"
          aria-modal="true"
          aria-label={active.title}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-xl"
        >
          <div className="w-full max-w-4xl" style={{ '--cat': active.hex } as React.CSSProperties}>
            <header className="mb-8 flex items-center gap-5">
              <span
                aria-hidden
                className="-rotate-2 select-none rounded-[3px] border-2 px-2 py-1 text-3xl font-black leading-none"
                style={{ borderColor: active.hex, color: active.hex }}
              >
                {active.glyph}
              </span>
              <h2 className="font-manga flex-1 text-4xl font-black uppercase italic tracking-tighter text-white">
                {active.title}
              </h2>
              <button
                onClick={onClose}
                aria-label="Fermer"
                className="rounded-full p-2 text-white transition-colors hover:bg-white/10"
              >
                <X className="h-8 w-8" />
              </button>
            </header>

            {/* Onglets : naviguer entre les catégories sans fermer le menu */}
            <nav
              aria-label="Catégories d'ateliers"
              className="mb-10 flex flex-wrap gap-2 border-b border-white/10 pb-4"
            >
              {categories.map((cat) => {
                const isActive = cat.id === selected;
                return (
                  <button
                    key={cat.id}
                    type="button"
                    onClick={() => onSelect(cat.id)}
                    aria-pressed={isActive}
                    className={`flex items-center gap-2 rounded-full border px-4 py-2 text-[10px] font-black uppercase tracking-widest transition-colors ${
                      isActive
                        ? 'text-black'
                        : 'border-white/15 text-white/50 hover:border-white/40 hover:text-white'
                    }`}
                    style={
                      isActive ? { backgroundColor: cat.hex, borderColor: cat.hex } : undefined
                    }
                  >
                    <span aria-hidden className="text-sm font-bold leading-none">
                      {cat.glyph}
                    </span>
                    {cat.title}
                  </button>
                );
              })}
            </nav>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
              {labs.map((lab, i) => (
                <motion.div
                  key={`${selected}-${lab.id}`}
                  initial={{ opacity: 0, y: 14 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, delay: i * 0.05 }}
                >
                  <Link key={lab.id} to={lab.url} className="group block no-underline">
                    <article className="flex items-center gap-5 rounded-2xl border border-white/10 bg-white/5 p-6 transition-all duration-300 group-hover:-translate-y-0.5 group-hover:border-[color:var(--cat)]">
                      {lab.glyph && (
                        <span
                          aria-hidden
                          className="select-none text-3xl font-black leading-none opacity-80"
                          style={{ color: active.hex }}
                        >
                          {lab.glyph}
                        </span>
                      )}
                      <div className="min-w-0 flex-1">
                        <h3 className="font-manga text-xl font-black uppercase italic text-white transition-colors group-hover:text-[color:var(--cat)]">
                          {lab.title}
                        </h3>
                        <p className="mt-1.5 text-xs leading-relaxed text-white/50">{lab.desc}</p>
                      </div>
                      <ArrowRight
                        className="h-6 w-6 -translate-x-2 text-white/0 transition-all group-hover:translate-x-0 group-hover:text-[color:var(--cat)]"
                        aria-hidden="true"
                      />
                    </article>
                  </Link>
                </motion.div>
              ))}
            </div>

            <p className="mt-8 text-center text-[10px] font-bold uppercase tracking-[0.3em] text-white/25">
              Échap pour fermer · clique un onglet pour changer de catégorie
            </p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
