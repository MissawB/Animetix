import React from 'react';
import { useTranslation } from 'react-i18next';
import { Swords, X } from 'lucide-react';
import { ArenaCharacter } from '../../../types';

export type Slot = 'A' | 'B';

const slotTheme = (slot: Slot) =>
  slot === 'A'
    ? {
        ring: 'border-red-500',
        soft: 'border-red-500/20 bg-red-500/5',
        text: 'text-red-500',
        dot: 'bg-red-500',
      }
    : {
        ring: 'border-blue-500',
        soft: 'border-blue-500/20 bg-blue-500/5',
        text: 'text-blue-500',
        dot: 'bg-blue-500',
      };

export const FighterSlot: React.FC<{
  slot: Slot;
  char: ArenaCharacter | null;
  active: boolean;
  onActivate: () => void;
  onClear: () => void;
}> = ({ slot, char, active, onActivate, onClear }) => {
  const { t } = useTranslation();
  const theme = slotTheme(slot);
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onActivate}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onActivate();
        }
      }}
      className={`relative w-full text-left rounded-[2rem] border-2 overflow-hidden transition-all aspect-[3/4] cursor-pointer ${
        active ? `${theme.ring} shadow-2xl scale-[1.02]` : theme.soft
      }`}
    >
      {char ? (
        <>
          <img
            src={char.image}
            alt={char.name}
            className="absolute inset-0 w-full h-full object-cover"
            loading="lazy"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              onClear();
            }}
            className="absolute top-3 right-3 z-10 w-8 h-8 grid place-items-center rounded-full bg-black/60 text-white hover:bg-red-600 transition-colors"
            aria-label={t('games.vs_battle.remove_fighter', 'Retirer le combattant')}
          >
            <X className="w-4 h-4" />
          </button>
          <div className="absolute bottom-0 left-0 right-0 p-4 z-10">
            <p className="font-black italic manga-font uppercase text-white leading-tight text-base sm:text-lg break-words">
              {char.name}
            </p>
            <p className="text-[10px] font-black uppercase tracking-widest text-white/60 leading-snug break-words mt-1">
              {char.franchise}
            </p>
          </div>
        </>
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-4 text-center">
          <div
            className={`w-14 h-14 rounded-2xl grid place-items-center ${theme.soft} border-2 ${active ? theme.ring : ''}`}
          >
            <Swords className={`w-7 h-7 ${theme.text}`} />
          </div>
          <p className={`font-black italic uppercase ${theme.text}`}>
            {t('games.vs_battle.challenger', { defaultValue: 'Challenger {{slot}}', slot })}
          </p>
          <p className="text-[10px] font-bold uppercase tracking-widest opacity-40">
            {active
              ? t('games.vs_battle.choose_below', 'Choisis ci-dessous')
              : t('games.vs_battle.tap_to_select', 'Touche pour sélectionner')}
          </p>
        </div>
      )}
    </div>
  );
};
