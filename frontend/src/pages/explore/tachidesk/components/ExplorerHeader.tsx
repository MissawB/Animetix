import React from 'react';
import { Link } from 'react-router-dom';
import { Library, ArrowLeft, RefreshCw } from 'lucide-react';

interface ExplorerHeaderProps {
  activeTab: 'catalog' | 'extensions';
  loadingSources: boolean;
  loadingExtensions: boolean;
  onSelectCatalogTab: () => void;
  onSelectExtensionsTab: () => void;
  onRefresh: () => void;
}

const tabClass = (active: boolean) =>
  `rounded-xl px-5 py-2 text-xs font-black uppercase italic tracking-wider transition-colors ${
    active
      ? 'bg-[#E8442B] text-[#F4F1E8]'
      : 'text-[#8F94A5] hover:bg-[#F4F1E8]/[0.04] hover:text-[#F4F1E8]'
  }`;

const ExplorerHeaderComponent: React.FC<ExplorerHeaderProps> = ({
  activeTab,
  loadingSources,
  loadingExtensions,
  onSelectCatalogTab,
  onSelectExtensionsTab,
  onRefresh,
}) => {
  const busy = loadingSources || loadingExtensions;
  return (
    <header className="sticky top-0 z-40 border-b border-[#F4F1E8]/10 bg-[#0B0C10]/85 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[110rem] flex-wrap items-center justify-between gap-4 px-6 py-4 sm:px-8">
        <div className="flex items-center gap-4">
          <Link
            to="/explore/"
            title="Retour à l'exploration"
            className="grid h-10 w-10 flex-none place-items-center rounded-full border border-[#F4F1E8]/15 text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <span className="explore-stamp hidden -rotate-2 sm:block" aria-hidden>
            蔵
          </span>
          <div>
            <div className="mb-0.5 flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              <Library className="h-3 w-3" /> Suwayomi · Bibliothèque
            </div>
            <h1 className="font-manga text-2xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-3xl">
              Explorateur<span className="text-[#E8442B]">.</span>
            </h1>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex gap-1.5 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-1.5">
            <button
              type="button"
              onClick={onSelectCatalogTab}
              className={tabClass(activeTab === 'catalog')}
            >
              Catalogue
            </button>
            <button
              type="button"
              onClick={onSelectExtensionsTab}
              className={tabClass(activeTab === 'extensions')}
            >
              Extensions
            </button>
          </div>

          <button
            type="button"
            onClick={onRefresh}
            disabled={busy}
            title={activeTab === 'catalog' ? 'Rafraîchir les sources' : 'Rafraîchir les extensions'}
            aria-label="Rafraîchir"
            className="grid h-11 w-11 place-items-center rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] text-[#8F94A5] transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8] disabled:opacity-50"
          >
            <RefreshCw className={`h-5 w-5 ${busy ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </header>
  );
};

export const ExplorerHeader = React.memo(ExplorerHeaderComponent);
