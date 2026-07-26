import React, { useEffect, useRef, useState } from 'react';
import { ChevronDown, Search } from 'lucide-react';
import { LAB_INPUT } from './shared/LabKit';

export interface ThemeOption {
  value: string;
  label: string;
}

/** Liste déroulante recherchable (façon « Sélecteur d'Univers » de la forge) :
 *  un déclencheur qui ouvre un panneau avec un champ de recherche + la liste
 *  filtrée. Accessible (listbox, aria-labelledby, Échap, clic extérieur). */
export const ThemeCombobox: React.FC<{
  value: string;
  onChange: (value: string) => void;
  options: ThemeOption[];
  labelId?: string;
}> = ({ value, onChange, options, labelId }) => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const ref = useRef<HTMLDivElement>(null);

  const selected = options.find((o) => o.value === value);
  const q = query.trim().toLowerCase();
  const filtered = q ? options.filter((o) => o.label.toLowerCase().includes(q)) : options;

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [open]);

  const select = (v: string) => {
    onChange(v);
    setOpen(false);
    setQuery('');
  };

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        onKeyDown={(e) => {
          if (e.key === 'Escape') setOpen(false);
        }}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-labelledby={labelId}
        className={`${LAB_INPUT} flex items-center justify-between text-left`}
      >
        <span className="truncate">{selected?.label ?? 'Choisir un thème'}</span>
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-[#8F94A5] transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden="true"
        />
      </button>

      {open && (
        <div className="absolute z-30 mt-2 w-full overflow-hidden rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] shadow-2xl animate-in fade-in slide-in-from-top-1 duration-150">
          <div className="flex items-center gap-2 border-b border-[#F4F1E8]/10 px-3">
            <Search className="h-3.5 w-3.5 shrink-0 text-[#8F94A5]" aria-hidden="true" />
            <input
              autoFocus
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') setOpen(false);
                if (e.key === 'Enter' && filtered[0]) {
                  e.preventDefault();
                  select(filtered[0].value);
                }
              }}
              placeholder="Rechercher un thème…"
              aria-label="Rechercher un thème"
              className="w-full bg-transparent py-2.5 text-sm text-[#F4F1E8] outline-none placeholder:text-[#8F94A5]/60"
            />
          </div>
          <ul role="listbox" className="custom-scrollbar max-h-60 overflow-y-auto p-1">
            {filtered.map((o) => (
              <li key={o.value}>
                <button
                  type="button"
                  role="option"
                  aria-selected={o.value === value}
                  onClick={() => select(o.value)}
                  className={`w-full rounded-lg px-3 py-2 text-left text-sm transition-colors ${
                    o.value === value
                      ? 'bg-[#FDB913]/10 font-bold text-[#FDB913]'
                      : 'text-[#F4F1E8] hover:bg-[#F4F1E8]/[0.06]'
                  }`}
                >
                  {o.label}
                </button>
              </li>
            ))}
            {filtered.length === 0 && (
              <li className="px-3 py-3 text-center text-sm text-[#8F94A5]">Aucun thème trouvé</li>
            )}
          </ul>
        </div>
      )}
    </div>
  );
};
