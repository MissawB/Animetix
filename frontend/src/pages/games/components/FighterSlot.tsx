import React from 'react';
import { useTranslation } from 'react-i18next';
import { Swords, X } from 'lucide-react';
import { ArenaCharacter } from '../../../types';

export type Slot = 'A' | 'B';

/** Les deux camps du kōhaku : A = rouge (shu), B = blanc (papier). */
const slotTheme = (slot: Slot) =>
  slot === 'A'
    ? {
        ring: 'border-[#E8442B]',
        soft: 'border-[#E8442B]/25 bg-[#E8442B]/5',
        text: 'text-[#E8442B]',
      }
    : {
        ring: 'border-[#F4F1E8]',
        soft: 'border-[#F4F1E8]/25 bg-[#F4F1E8]/5',
        text: 'text-[#F4F1E8]',
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
      className={`relative w-full text-left rounded-2xl border-2 overflow-hidden transition-all aspect-[3/4] cursor-pointer focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] ${
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
            className="absolute top-3 right-3 z-10 w-8 h-8 grid place-items-center rounded-full bg-black/60 text-white hover:bg-[#E8442B] transition-colors"
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
            className={`w-14 h-14 rounded-xl grid place-items-center ${theme.soft} border-2 ${active ? theme.ring : ''}`}
          >
            <Swords className={`w-7 h-7 ${theme.text}`} />
          </div>
          <p className={`font-black italic uppercase ${theme.text}`}>
            {t('games.vs_battle.challenger', { defaultValue: 'Challenger {{slot}}', slot })}
          </p>
          <p className="text-[10px] font-bold uppercase tracking-widest text-[#8F94A5]">
            {active
              ? t('games.vs_battle.choose_below', 'Choisis ci-dessous')
              : t('games.vs_battle.tap_to_select', 'Touche pour sélectionner')}
          </p>
        </div>
      )}
    </div>
  );
};
