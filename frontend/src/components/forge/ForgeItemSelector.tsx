import React from 'react';
import { useTranslation } from 'react-i18next';
import { X, Info, Sparkles } from 'lucide-react';
import { SearchBar } from '../SearchBar';
import { SearchItem } from '../../types';

interface ForgeItemSelectorProps {
  itemA: SearchItem | null;
  setItemA: (item: SearchItem | null) => void;
  itemB: SearchItem | null;
  setItemB: (item: SearchItem | null) => void;
}

export const ForgeItemSelector: React.FC<ForgeItemSelectorProps> = ({
  itemA,
  setItemA,
  itemB,
  setItemB,
}) => {
  const { t } = useTranslation();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label htmlFor="univers-alpha" className="text-[10px] font-black uppercase tracking-widest opacity-70">
            {t('games.forge.universe_alpha', 'Univers Alpha')}
          </label>
          {itemA && (
            <button
              onClick={() => setItemA(null)}
              className="text-[10px] font-bold text-red-500 hover:underline flex items-center gap-1"
            >
              <X className="w-2 h-2" /> {t('games.forge.clear', 'Effacer')}
            </button>
          )}
        </div>
        <SearchBar
          id="univers-alpha"
          onSelect={setItemA}
          placeholder={t('games.forge.search_placeholder', 'Rechercher...')}
        />

        <div className="h-[180px] relative overflow-hidden rounded-3xl bg-black/5 dark:bg-white/5 border border-dashed border-black/10 dark:border-white/10 flex items-center justify-center group transition-all">
          {itemA ? (
            <>
              <img
                src={itemA.image_url}
                className="absolute inset-0 w-full h-full object-cover brightness-50 group-hover:scale-110 transition-transform duration-500"
                alt=""
                loading="lazy"
                decoding="async"
              />
              <div className="relative z-10 text-center p-4">
                <div className="font-black italic text-white uppercase drop-shadow-md leading-tight mb-1">
                  {itemA.title || itemA.name}
                </div>
                <div className="text-[9px] bg-white/20 backdrop-blur-md text-white font-bold px-2 py-0.5 rounded-full inline-block uppercase">
                  {itemA.type}
                </div>
              </div>
            </>
          ) : (
            <div className="text-center opacity-40 group-hover:opacity-70 transition-opacity">
              <div className="w-12 h-12 bg-black/10 dark:bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-2">
                <Info className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-black uppercase tracking-widest">
                {t('games.forge.choose_origin', "Choisir l'origine")}
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="hidden md:flex absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-yellow-400 text-black rounded-2xl items-center justify-center z-20 shadow-lg shadow-yellow-400/40 ring-4 ring-cyberpunk-bg rotate-12">
        <Sparkles className="w-6 h-6" strokeWidth={2.5} />
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label htmlFor="univers-beta" className="text-[10px] font-black uppercase tracking-widest opacity-70">
            {t('games.forge.universe_beta', 'Univers Bêta')}
          </label>
          {itemB && (
            <button
              onClick={() => setItemB(null)}
              className="text-[10px] font-bold text-red-500 hover:underline flex items-center gap-1"
            >
              <X className="w-2 h-2" /> {t('games.forge.clear', 'Effacer')}
            </button>
          )}
        </div>
        <SearchBar
          id="univers-beta"
          onSelect={setItemB}
          placeholder={t('games.forge.search_placeholder', 'Rechercher...')}
        />

        <div className="h-[180px] relative overflow-hidden rounded-3xl bg-black/5 dark:bg-white/5 border border-dashed border-black/10 dark:border-white/10 flex items-center justify-center group transition-all">
          {itemB ? (
            <>
              <img
                src={itemB.image_url}
                className="absolute inset-0 w-full h-full object-cover brightness-50 group-hover:scale-110 transition-transform duration-500"
                alt=""
                loading="lazy"
                decoding="async"
              />
              <div className="relative z-10 text-center p-4">
                <div className="font-black italic text-white uppercase drop-shadow-md leading-tight mb-1">
                  {itemB.title || itemB.name}
                </div>
                <div className="text-[9px] bg-white/20 backdrop-blur-md text-white font-bold px-2 py-0.5 rounded-full inline-block uppercase">
                  {itemB.type}
                </div>
              </div>
            </>
          ) : (
            <div className="text-center opacity-40 group-hover:opacity-70 transition-opacity">
              <div className="w-12 h-12 bg-black/10 dark:bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-2">
                <Info className="w-6 h-6" />
              </div>
              <span className="text-[10px] font-black uppercase tracking-widest">
                {t('games.forge.choose_origin', "Choisir l'origine")}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
