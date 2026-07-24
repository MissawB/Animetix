import React from 'react';
import { Clapperboard, BookOpen, Users } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export type Universe = 'Anime' | 'Manga' | 'Character';

interface ClassicUniverseSelectorProps {
  universe: Universe;
  setUniverse: (u: Universe) => void;
}

export const ClassicUniverseSelector: React.FC<ClassicUniverseSelectorProps> = ({
  universe,
  setUniverse,
}) => {
  const { t } = useTranslation();

  const UNIVERSES: { key: Universe; label: string; sub: string; icon: React.ElementType }[] = [
    {
      key: 'Anime',
      label: t('games.classic.lobby.universes.anime.label', 'Anime'),
      sub: t('games.classic.lobby.universes.anime.sub', 'Séries animées'),
      icon: Clapperboard,
    },
    {
      key: 'Manga',
      label: t('games.classic.lobby.universes.manga.label', 'Manga'),
      sub: t('games.classic.lobby.universes.manga.sub', 'Œuvres papier'),
      icon: BookOpen,
    },
    {
      key: 'Character',
      label: t('games.classic.lobby.universes.character.label', 'Personnages'),
      sub: t('games.classic.lobby.universes.character.sub', 'Héros & figures'),
      icon: Users,
    },
  ];

  return (
    <div className="grid grid-cols-3 gap-3 sm:gap-4">
      {UNIVERSES.map(({ key, label, sub, icon: Icon }) => (
        <button
          key={key}
          onClick={() => setUniverse(key)}
          aria-pressed={universe === key}
          className={`flex flex-col items-center gap-3 p-5 sm:p-6 rounded-2xl border-2 transition-colors ${
            universe === key
              ? 'border-[#FDB913] bg-[#FDB913]/10'
              : 'border-[#F4F1E8]/10 hover:border-[#FDB913]/50'
          }`}
        >
          <Icon
            className={`w-8 h-8 sm:w-9 sm:h-9 ${universe === key ? 'text-[#FDB913]' : 'text-[#8F94A5]'}`}
          />
          <span className="font-manga text-base sm:text-lg text-[#F4F1E8] text-center leading-none">
            {label}
          </span>
          <span className="text-[10px] sm:text-[11px] font-bold uppercase tracking-widest text-[#8F94A5] text-center">
            {sub}
          </span>
        </button>
      ))}
    </div>
  );
};
