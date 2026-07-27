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

const SECTION = 'flex items-center gap-2 font-manga text-xs font-black uppercase tracking-widest';
const GRID = 'grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3';

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
    <main className="flex-1 space-y-6 overflow-y-auto px-6 py-8 sm:px-8">
      {/* Barre de recherche des extensions */}
      <div className="flex flex-col items-stretch justify-between gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:flex-row sm:items-center">
        <div className="relative w-full max-w-md">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8F94A5]/60" />
          <input
            type="text"
            value={extensionSearchQuery}
            onChange={(e) => onSearchQueryChange(e.target.value)}
            aria-label="Rechercher une extension"
            placeholder="Rechercher une extension par nom ou langue (ex : en, fr)…"
            className="w-full rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] py-3 pl-11 pr-4 text-sm font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
          />
        </div>
        <div className="text-xs font-black uppercase tracking-wider tabular-nums text-[#8F94A5]">
          Total : {filteredExtensions.length} / {extensions.length} extensions
        </div>
      </div>

      {loadingExtensions ? (
        <div className="flex flex-col items-center justify-center gap-4 py-32">
          <Loader2 className="h-8 w-8 animate-spin text-[#FDB913]" />
          <p className="text-sm font-semibold text-[#8F94A5]">
            Récupération de la liste des extensions…
          </p>
        </div>
      ) : (
        <div className="space-y-8">
          {updateExtensions.length > 0 && (
            <div className="space-y-4">
              <h3 className={`${SECTION} text-[#5D7FD3]`}>
                <ArrowUpCircle className="h-4 w-4" /> Mises à jour disponibles (
                {updateExtensions.length})
              </h3>
              <div className={GRID}>
                {updateExtensions.map((ext) => (
                  <ExtensionRow
                    key={ext.pkgName}
                    ext={ext}
                    onAction={onAction}
                    inProgress={actionProgress[ext.pkgName]}
                    getProxiedImageUrl={getProxiedImageUrl}
                  />
                ))}
              </div>
            </div>
          )}

          <div className="space-y-4">
            <h3 className={`${SECTION} text-[#8F94A5]`}>
              <CheckCircle className="h-4 w-4 text-[#FDB913]" /> Extensions installées (
              {installedExtensions.length})
            </h3>
            {installedExtensions.length === 0 ? (
              <p className="text-xs italic text-[#8F94A5]/70">
                Aucune extension installée actuellement.
              </p>
            ) : (
              <div className={GRID}>
                {installedExtensions.map((ext) => (
                  <ExtensionRow
                    key={ext.pkgName}
                    ext={ext}
                    onAction={onAction}
                    inProgress={actionProgress[ext.pkgName]}
                    getProxiedImageUrl={getProxiedImageUrl}
                  />
                ))}
              </div>
            )}
          </div>

          <div className="space-y-4">
            <h3 className={`${SECTION} text-[#8F94A5]`}>
              <Globe className="h-4 w-4 text-[#5D7FD3]" /> Extensions disponibles (
              {availableExtensions.length})
            </h3>
            {availableExtensions.length === 0 ? (
              <p className="text-xs italic text-[#8F94A5]/70">
                Aucune extension disponible correspondante.
              </p>
            ) : (
              <div className={GRID}>
                {availableExtensions.map((ext) => (
                  <ExtensionRow
                    key={ext.pkgName}
                    ext={ext}
                    onAction={onAction}
                    inProgress={actionProgress[ext.pkgName]}
                    getProxiedImageUrl={getProxiedImageUrl}
                  />
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
