import React from 'react';
import { createPortal } from 'react-dom';
import { Play } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { StreamingPlatform } from '../../../types';

const BTN_CLASS =
  'inline-flex items-center gap-2 px-5 py-2.5 bg-yellow-400 text-black rounded-lg font-black uppercase italic text-sm no-underline border-none cursor-pointer';

export const WatchButton: React.FC<{ title: string; platforms: StreamingPlatform[] }> = ({
  title,
  platforms,
}) => {
  const { t } = useTranslation();
  const [open, setOpen] = React.useState(false);
  const btnRef = React.useRef<HTMLButtonElement>(null);
  const [pos, setPos] = React.useState({ top: 0, left: 0 });

  React.useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    const onClick = (e: MouseEvent) => {
      if (btnRef.current && !btnRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('keydown', onKey);
    document.addEventListener('mousedown', onClick);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('mousedown', onClick);
    };
  }, [open]);

  const label = t('media.detail.where_to_watch', 'Où regarder');

  if (platforms.length === 0) {
    return (
      <a
        href={`https://www.justwatch.com/fr/recherche?q=${encodeURIComponent(title)}`}
        target="_blank"
        rel="noopener noreferrer"
        className={BTN_CLASS}
      >
        <Play className="w-5 h-5" aria-hidden="true" /> {label}
      </a>
    );
  }

  const toggle = () => {
    if (!open && btnRef.current) {
      const r = btnRef.current.getBoundingClientRect();
      setPos({ top: r.bottom + 8, left: r.left });
    }
    setOpen((o) => !o);
  };

  return (
    <>
      <button ref={btnRef} onClick={toggle} className={BTN_CLASS} aria-expanded={open}>
        <Play className="w-5 h-5" aria-hidden="true" /> {label}
      </button>
      {open &&
        createPortal(
          <div
            className="fixed w-64 bg-gray-900 border border-white/10 rounded-xl shadow-2xl p-3 space-y-2 z-50"
            style={{ top: pos.top, left: pos.left }}
          >
            {platforms.map((p) => (
              <div
                key={p.platform}
                className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-white/5"
              >
                <span className="text-xs font-bold text-white">{p.platform}</span>
                <span className="flex gap-1">
                  {p.has_vostfr && (
                    <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400">
                      VOSTFR
                    </span>
                  )}
                  {p.has_vf && (
                    <span className="text-[9px] font-black px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400">
                      VF
                    </span>
                  )}
                </span>
              </div>
            ))}
            <p className="text-[9px] text-gray-500 uppercase tracking-widest px-2">
              {t('media.detail.watch_source', 'Données du catalogue')}
            </p>
          </div>,
          document.body,
        )}
    </>
  );
};
