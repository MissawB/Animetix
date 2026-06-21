import React from 'react';
import { Search, Loader2, CheckCircle, Globe, ArrowUpCircle } from 'lucide-react';
import { ExtensionRow } from './ExtensionRow';
import type { Extension, ExtensionAction } from '../types';

interface ExtensionsTabProps {
  extensions: Extension[];
  filteredExtensions: Extension[];
  updateExtensions: Extension[];
  installedExtensions: Extension[];
  availableExtensions: Extension[];
  extensionSearchQuery: string;
  loadingExtensions: boolean;
  actionProgress: Record<string, boolean>;
  onSearchQueryChange: (value: string) => void;
  onAction: (pkgName: string, action: ExtensionAction) => void;
  getProxiedImageUrl: (url: string) => string;
}

const ExtensionsTabComponent: React.FC<ExtensionsTabProps> = ({
  extensions,
  filteredExtensions,
  updateExtensions,
  installedExtensions,
  availableExtensions,
  extensionSearchQuery,
  loadingExtensions,
  actionProgress,
  onSearchQueryChange,
  onAction,
  getProxiedImageUrl,
}) => {
  return (
    <main className="flex-1 overflow-y-auto px-8 py-8 space-y-6">
      {/* Search Bar for extensions */}
      <div className="bg-navy-950/20 backdrop-blur-md border border-white/5 p-6 rounded-3xl flex justify-between items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            value={extensionSearchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            aria-label="Rechercher une extension"
            placeholder="Rechercher une extension par nom ou langue (ex: en, fr)..."
            className="w-full bg-[#0d0d1b] border border-white/10 rounded-xl pl-11 pr-4 py-3 text-sm focus:outline-none focus:border-blue-500 font-medium"
          />
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        </div>
        <div className="text-xs text-gray-400 font-semibold uppercase tracking-wider">
          Total : {filteredExtensions.length} / {extensions.length} extensions
        </div>
      </div>

      {loadingExtensions ? (
        <div className="flex flex-col items-center justify-center py-32 gap-4">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
          <p className="text-gray-400 text-sm font-semibold">Récupération de la liste des extensions...</p>
        </div>
      ) : (
        <div className="space-y-8">
          {/* CATEGORY 1: Updates Available */}
          {updateExtensions.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-xs font-black uppercase tracking-widest text-blue-500 flex items-center gap-2">
                <ArrowUpCircle className="w-4 h-4" /> Mises à jour disponibles ({updateExtensions.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {updateExtensions.map((ext) => (
                  <ExtensionRow key={ext.pkgName} ext={ext} onAction={onAction} inProgress={actionProgress[ext.pkgName]} getProxiedImageUrl={getProxiedImageUrl} />
                ))}
              </div>
            </div>
          )}

          {/* CATEGORY 2: Installed Extensions */}
          <div className="space-y-4">
            <h3 className="text-xs font-black uppercase tracking-widest text-gray-400 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" /> Extensions Installées ({installedExtensions.length})
            </h3>
            {installedExtensions.length === 0 ? (
              <p className="text-xs text-gray-500 italic">Aucune extension installée actuellement.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {installedExtensions.map((ext) => (
                  <ExtensionRow key={ext.pkgName} ext={ext} onAction={onAction} inProgress={actionProgress[ext.pkgName]} getProxiedImageUrl={getProxiedImageUrl} />
                ))}
              </div>
            )}
          </div>

          {/* CATEGORY 3: Available Extensions */}
          <div className="space-y-4">
            <h3 className="text-xs font-black uppercase tracking-widest text-gray-400 flex items-center gap-2">
              <Globe className="w-4 h-4 text-blue-500" /> Extensions Disponibles ({availableExtensions.length})
            </h3>
            {availableExtensions.length === 0 ? (
              <p className="text-xs text-gray-500 italic">Aucune extension disponible correspondante.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {availableExtensions.map((ext) => (
                  <ExtensionRow key={ext.pkgName} ext={ext} onAction={onAction} inProgress={actionProgress[ext.pkgName]} getProxiedImageUrl={getProxiedImageUrl} />
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
};

export const ExtensionsTab = React.memo(ExtensionsTabComponent);
