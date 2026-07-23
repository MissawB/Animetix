import React from 'react';
import { Search, Loader2, Globe, Database } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { LAB_INPUT } from './shared/LabKit';

/** Bouton de recherche compact, même voix que LAB_CTA. */
const SEARCH_BTN =
  'inline-flex cursor-pointer items-center gap-2 rounded-lg border-none bg-[#E8442B] px-6 py-2.5 font-manga text-sm font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50';

interface SeiyuuSearchFiltersPanelProps {
  searchQuery: string;
  setSearchQuery: (val: string) => void;
  langFilter: string;
  setLangFilter: (val: string) => void;
  originFilter: string;
  setOriginFilter: (val: string) => void;
  isLoading: boolean;
  isRefetching: boolean;
  onSearch: (e: React.FormEvent) => void;
}

export const SeiyuuSearchFiltersPanel: React.FC<SeiyuuSearchFiltersPanelProps> = ({
  searchQuery,
  setSearchQuery,
  langFilter,
  setLangFilter,
  originFilter,
  setOriginFilter,
  isLoading,
  isRefetching,
  onSearch,
}) => {
  const { t } = useTranslation();

  return (
    <div className="mb-12 space-y-6">
      <form onSubmit={onSearch} className="relative">
        <input
          type="text"
          aria-label={t(
            'labs.seiyuu.search_placeholder',
            'Chercher par nom de doubleur ou de personnage',
          )}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={t(
            'labs.seiyuu.search_placeholder',
            'Chercher par nom de doubleur ou nom de personnage...',
          )}
          className={`${LAB_INPUT} py-5 pr-44 text-base`}
        />
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          <button type="submit" disabled={isLoading || isRefetching} className={SEARCH_BTN}>
            {isLoading || isRefetching ? (
              <Loader2 className="h-5 w-5 animate-spin" aria-hidden="true" />
            ) : (
              <>
                <Search className="h-4 w-4" aria-hidden="true" />{' '}
                {t('labs.seiyuu.btn_search', 'RECHERCHER')}
              </>
            )}
          </button>
        </div>
      </form>

      {/* Quick Filters */}
      <div className="flex flex-wrap items-center justify-between gap-6">
        <div className="flex flex-wrap items-center gap-4">
          <span className="flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
            <Globe className="h-3 w-3" aria-hidden="true" />{' '}
            {t('labs.seiyuu.filter_lang', 'Langue:')}
          </span>
          <div className="flex gap-2">
            {[
              { label: t('labs.seiyuu.filter_all', 'Tous'), value: '' },
              { label: t('labs.seiyuu.lang_option_ja', 'Japonais (Seiyuu)'), value: 'japanese' },
              { label: t('labs.seiyuu.lang_option_fr', 'Français (Doubleur)'), value: 'french' },
            ].map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setLangFilter(opt.value)}
                className={`cursor-pointer rounded-xl border px-4 py-2 text-[10px] font-black uppercase tracking-wider transition-colors ${
                  langFilter === opt.value
                    ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]'
                    : 'border-[#F4F1E8]/10 bg-transparent text-[#8F94A5] hover:border-[#F4F1E8]/25 hover:text-[#F4F1E8]'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <span className="flex items-center gap-1 text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
            <Database className="h-3 w-3" aria-hidden="true" />{' '}
            {t('labs.seiyuu.filter_origin', 'Origine:')}
          </span>
          <div className="flex gap-2">
            {[
              { label: t('labs.seiyuu.filter_all', 'Tous'), value: '' },
              { label: t('labs.seiyuu.origin_dataset', 'Dataset HF'), value: 'dataset' },
              { label: t('labs.seiyuu.origin_youtube', 'YouTube Ingest'), value: 'youtube' },
            ].map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setOriginFilter(opt.value)}
                className={`cursor-pointer rounded-xl border px-4 py-2 text-[10px] font-black uppercase tracking-wider transition-colors ${
                  originFilter === opt.value
                    ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#FDB913]'
                    : 'border-[#F4F1E8]/10 bg-transparent text-[#8F94A5] hover:border-[#F4F1E8]/25 hover:text-[#F4F1E8]'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
