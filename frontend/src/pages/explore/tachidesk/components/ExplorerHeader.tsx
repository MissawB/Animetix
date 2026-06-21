import React from 'react';
import { Link } from 'react-router-dom';
import { Globe, ArrowLeft, RefreshCw } from 'lucide-react';

interface ExplorerHeaderProps {
  activeTab: 'catalog' | 'extensions';
  loadingSources: boolean;
  loadingExtensions: boolean;
  onSelectCatalogTab: () => void;
  onSelectExtensionsTab: () => void;
  onRefresh: () => void;
}

const ExplorerHeaderComponent: React.FC<ExplorerHeaderProps> = ({
  activeTab,
  loadingSources,
  loadingExtensions,
  onSelectCatalogTab,
  onSelectExtensionsTab,
  onRefresh,
}) => {
  return (
    <header className="bg-navy-950/40 backdrop-blur-xl border-b border-white/5 px-8 py-4 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-6">
        <Link to="/explore/" className="p-2 hover:bg-white/5 rounded-full transition-colors text-white">
          <ArrowLeft className="w-6 h-6" />
        </Link>
        <div>
          <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-blue-500 mb-0.5">
            <Globe className="w-3.5 h-3.5" />
            Mihon Integration
          </div>
          <h1 className="text-2xl font-black italic uppercase tracking-tight flex items-center gap-2">
            Tachidesk Explorer
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Tab Selector */}
        <div className="bg-navy-900/60 p-1.5 rounded-2xl flex gap-1 border border-white/5">
          <button
            onClick={onSelectCatalogTab}
            className={`px-5 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all ${
              activeTab === 'catalog'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/10'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Catalogue
          </button>
          <button
            onClick={onSelectExtensionsTab}
            className={`px-5 py-2 rounded-xl text-xs font-black uppercase tracking-wider transition-all ${
              activeTab === 'extensions'
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/10'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            Extensions
          </button>
        </div>

        <button
          onClick={onRefresh}
          disabled={loadingSources || loadingExtensions}
          className="p-3 bg-white/5 hover:bg-white/10 rounded-2xl transition-all border border-white/5 disabled:opacity-50"
          title={activeTab === 'catalog' ? "Rafraîchir les sources" : "Rafraîchir les extensions"}
        >
          <RefreshCw className={`w-5 h-5 opacity-60 ${(loadingSources || loadingExtensions) ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </header>
  );
};

export const ExplorerHeader = React.memo(ExplorerHeaderComponent);
