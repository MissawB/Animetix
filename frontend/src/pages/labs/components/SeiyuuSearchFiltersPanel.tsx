import React from 'react';
import { Search, Loader2, Globe, Database } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Button } from '../../../components/ui/Button';

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
      <form onSubmit={onSearch} className="relative group">
        <div className="absolute inset-0 bg-emerald-500/20 blur-3xl opacity-0 group-focus-within:opacity-100 transition-opacity -z-10" />
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
          className="w-full bg-black/40 backdrop-blur-xl border-2 border-white/5 focus:border-emerald-500/50 rounded-[2.5rem] px-10 py-8 text-xl font-bold outline-none transition-all text-white placeholder:text-white/10"
        />
        <div className="absolute right-4 top-1/2 -translate-y-1/2 flex gap-4">
          <Button
            type="submit"
            disabled={isLoading || isRefetching}
            className="bg-emerald-600 hover:bg-emerald-500 text-white px-10 py-5 rounded-2xl font-black italic uppercase shadow-xl transition-all border-none flex items-center gap-3"
          >
            {isLoading || isRefetching ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Search className="w-5 h-5" /> {t('labs.seiyuu.btn_search', 'RECHERCHER')}
              </>
            )}
          </Button>
        </div>
      </form>

      {/* Quick Filters */}
      <div className="flex flex-wrap items-center justify-between gap-6 px-4">
        <div className="flex flex-wrap gap-4 items-center">
          <span className="text-[9px] font-black uppercase tracking-widest text-white/30 flex items-center gap-1">
            <Globe className="w-3 h-3" /> {t('labs.seiyuu.filter_lang', 'Langue:')}
          </span>
          <div className="flex gap-2">
            {[
              { label: t('labs.seiyuu.filter_all', 'Tous'), value: '' },
              { label: t('labs.seiyuu.lang_option_ja', 'Japonais (Seiyuu)'), value: 'japanese' },
              { label: t('labs.seiyuu.lang_option_fr', 'Français (Doubleur)'), value: 'french' },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setLangFilter(opt.value)}
                className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all border ${
                  langFilter === opt.value
                    ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400'
                    : 'bg-white/5 border-white/5 text-white/60 hover:border-white/10 hover:text-white'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-4 items-center">
          <span className="text-[9px] font-black uppercase tracking-widest text-white/30 flex items-center gap-1">
            <Database className="w-3 h-3" /> {t('labs.seiyuu.filter_origin', 'Origine:')}
          </span>
          <div className="flex gap-2">
            {[
              { label: t('labs.seiyuu.filter_all', 'Tous'), value: '' },
              { label: t('labs.seiyuu.origin_dataset', 'Dataset HF'), value: 'dataset' },
              { label: t('labs.seiyuu.origin_youtube', 'YouTube Ingest'), value: 'youtube' },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setOriginFilter(opt.value)}
                className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all border ${
                  originFilter === opt.value
                    ? 'bg-emerald-500/10 border-emerald-500 text-emerald-400'
                    : 'bg-white/5 border-white/5 text-white/60 hover:border-white/10 hover:text-white'
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
