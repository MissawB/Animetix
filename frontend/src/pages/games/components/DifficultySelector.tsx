import React from 'react';

export interface DifficultyOption<K extends string> {
  key: K;
  label: string;
  /** Optional second line (essais, public visé…). */
  sub?: string;
  /** Tailwind classes applied when this option is selected (border + bg + text). */
  active: string;
}

export interface DifficultySelectorProps<K extends string> {
  options: DifficultyOption<K>[];
  value: K;
  onChange: (key: K) => void;
  /** Grid wrapper classes — column count varies per lobby. */
  gridClassName?: string;
  /** Hover border of the *inactive* buttons — accent varies per lobby. */
  hoverClassName?: string;
}

/**
 * Sélecteur de difficulté partagé par les lobbies Akinetix / Classic / Covertest
 * (bouton "flex-col" avec label + sous-titre optionnel, état sélectionné via
 * `aria-pressed`). Factorisé depuis 3 copies identiques (audit dette 2026-07-19).
 *
 * Le lobby Blindtest garde son propre sélecteur compact (chips mono-ligne sans
 * sous-titre) — un style volontairement différent, hors périmètre de ce composant.
 */
export function DifficultySelector<K extends string>({
  options,
  value,
  onChange,
  gridClassName = 'grid grid-cols-2 sm:grid-cols-4 gap-3',
  hoverClassName = 'hover:border-blue-500/40',
}: DifficultySelectorProps<K>) {
  return (
    <div className={gridClassName}>
      {options.map((d) => (
        <button
          key={d.key}
          onClick={() => onChange(d.key)}
          aria-pressed={value === d.key}
          className={`flex flex-col items-center gap-1 py-4 rounded-2xl border-2 transition-all ${
            value === d.key
              ? d.active
              : `border-black/5 dark:border-white/10 text-gray-500 dark:text-gray-400 ${hoverClassName}`
          }`}
        >
          <span className="font-black italic uppercase tracking-wide text-sm">{d.label}</span>
          {d.sub && (
            <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">
              {d.sub}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}
