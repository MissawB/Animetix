import React from 'react';
import { useTranslation } from 'react-i18next';
import { Search, Loader2 } from 'lucide-react';
import { ArenaCharacter } from '../../../types';

interface Props {
  query: string;
  onQueryChange: (value: string) => void;
  isLoading: boolean;
  filtered: ArenaCharacter[];
  selectedA: ArenaCharacter | null;
  selectedB: ArenaCharacter | null;
  onPick: (c: ArenaCharacter) => void;
}

export const VsRosterPicker: React.FC<Props> = ({
  query,
  onQueryChange,
  isLoading,
  filtered,
  selectedA,
  selectedB,
  onPick,
}) => {
  const { t } = useTranslation();
  return (
    <div className="rounded-[2rem] border-2 border-white/5 bg-navy-900/40 p-5 md:p-6">
      <div className="relative mb-4">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 opacity-30 pointer-events-none" />
        <input
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder={t(
            'games.vs_battle.search_placeholder',
            'Rechercher un personnage ou une franchise…',
          )}
          aria-label={t('games.vs_battle.search_aria', 'Rechercher un personnage ou une franchise')}
          className="w-full pl-12 pr-4 py-3.5 rounded-2xl bg-black border-2 border-white/5 focus:border-red-500 outline-none font-bold transition-all placeholder:opacity-30"
        />
      </div>

      {isLoading ? (
        <div className="flex items-center gap-3 justify-center py-10 opacity-50 font-black uppercase tracking-widest text-sm">
          <Loader2 className="w-5 h-5 animate-spin" />{' '}
          {t('games.vs_battle.loading_roster', 'Chargement du roster…')}
        </div>
      ) : filtered.length === 0 ? (
        <p className="text-center py-10 opacity-30 font-black italic uppercase">
          {t('games.vs_battle.no_character', 'Aucun personnage trouvé')}
        </p>
      ) : (
        <div className="flex items-start gap-3 overflow-x-auto pb-3 -mx-1 px-1 snap-x [&::-webkit-scrollbar]:h-2.5 [&::-webkit-scrollbar-track]:bg-white/5 [&::-webkit-scrollbar-track]:rounded-full [&::-webkit-scrollbar-thumb]:bg-red-600/70 [&::-webkit-scrollbar-thumb]:rounded-full hover:[&::-webkit-scrollbar-thumb]:bg-red-500 [scrollbar-width:thin] [scrollbar-color:rgb(220_38_38_/_0.7)_rgba(255,255,255,0.05)]">
          {filtered.map((c) => {
            const isA = selectedA?.name === c.name && selectedA?.franchise === c.franchise;
            const isB = selectedB?.name === c.name && selectedB?.franchise === c.franchise;
            const both = isA && isB;
            return (
              <button
                type="button"
                key={`${c.name}|${c.franchise}`}
                onClick={() => onPick(c)}
                title={`${c.name} — ${c.franchise}`}
                className={`group shrink-0 w-32 snap-start rounded-2xl overflow-hidden border-2 transition-all hover:scale-[1.03] bg-black/30 ${
                  both
                    ? 'border-fuchsia-500 shadow-lg shadow-fuchsia-500/20'
                    : isA
                      ? 'border-red-500 shadow-lg shadow-red-500/20'
                      : isB
                        ? 'border-blue-500 shadow-lg shadow-blue-500/20'
                        : 'border-white/5 hover:border-white/20'
                }`}
              >
                <div className="relative aspect-[3/4] bg-navy-900">
                  <img
                    src={c.image}
                    alt={c.name}
                    className="w-full h-full object-cover"
                    loading="lazy"
                    decoding="async"
                  />
                  {c.source === 'synthetic' && (
                    <span
                      className="absolute bottom-1.5 left-1.5 text-[8px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded bg-black/70 text-white/70"
                      title={t(
                        'games.vs_battle.synthetic_title',
                        "Fiche générée par l'IA (pas de page VS Battles Wiki)",
                      )}
                    >
                      {t('games.vs_battle.ai_badge', 'IA')}
                    </span>
                  )}
                  {(isA || isB) && (
                    <div className="absolute top-1.5 right-1.5 flex gap-1">
                      {isA && (
                        <span className="w-6 h-6 grid place-items-center rounded-full text-white text-[10px] font-black bg-red-600">
                          A
                        </span>
                      )}
                      {isB && (
                        <span className="w-6 h-6 grid place-items-center rounded-full text-white text-[10px] font-black bg-blue-600">
                          B
                        </span>
                      )}
                    </div>
                  )}
                </div>
                <div className="p-2.5">
                  <p className="text-[11px] font-black italic uppercase leading-tight break-words text-white">
                    {c.name}
                  </p>
                  <p className="text-[8px] font-bold uppercase tracking-wider opacity-40 leading-snug break-words mt-1">
                    {c.franchise}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      )}
      <p className="text-[10px] font-black uppercase tracking-widest opacity-30 mt-2 text-center">
        {query
          ? t('games.vs_battle.results_count', {
              defaultValue: '{{count}} résultat{{plural}}',
              count: filtered.length,
              plural: filtered.length > 1 ? 's' : '',
            })
          : t(
              'games.vs_battle.scroll_hint',
              'Fais défiler le roster ou filtre par nom / franchise',
            )}
      </p>
    </div>
  );
};
