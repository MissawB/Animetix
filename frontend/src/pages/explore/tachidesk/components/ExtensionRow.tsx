import React from 'react';
import { Loader2, Download, Trash2, ArrowUpCircle } from 'lucide-react';
import type { Extension, ExtensionAction } from '../types';

interface ExtensionRowProps {
  ext: Extension;
  onAction: (pkgName: string, action: ExtensionAction) => void;
  inProgress: boolean;
  getProxiedImageUrl: (url: string) => string;
}

const ExtensionRowComponent: React.FC<ExtensionRowProps> = ({ ext, onAction, inProgress, getProxiedImageUrl }) => {
  return (
    <div className="p-4 bg-[#0c0c1b]/60 hover:bg-[#0c0c1b]/95 border border-white/5 hover:border-white/10 rounded-2xl flex items-center gap-4 transition-all group">
      {/* Icon */}
      <img
        src={getProxiedImageUrl(ext.iconUrl)}
        alt={ext.name}
        className="w-10 h-10 object-contain bg-white/5 p-1 rounded-xl border border-white/5 flex-shrink-0"
        onError={(e) => {
          e.currentTarget.src = 'https://via.placeholder.com/150?text=Manga';
        }}
        loading="lazy"
        decoding="async"
      />

      {/* Info details */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-bold text-gray-200 line-clamp-1 group-hover:text-blue-400 transition-colors">
            {ext.name}
          </h4>
          <span className="text-[8px] bg-white/5 text-gray-400 px-2 py-0.5 rounded-full font-black uppercase tracking-wider">
            {ext.lang}
          </span>
        </div>
        <p className="text-[10px] text-gray-500 font-medium truncate mt-0.5">
          v{ext.versionName}
        </p>

        {/* Dynamic Warning Badges */}
        <div className="flex gap-1.5 mt-1.5">
          {ext.isNsfw && (
            <span className="bg-red-500/10 text-red-500 border border-red-500/10 text-[7px] font-black uppercase px-1.5 py-0.5 rounded tracking-widest">
              18+
            </span>
          )}
          {ext.isObsolete && (
            <span className="bg-yellow-500/10 text-yellow-500 border border-yellow-500/10 text-[7px] font-black uppercase px-1.5 py-0.5 rounded tracking-widest">
              Obsolète
            </span>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex-shrink-0">
        {ext.hasUpdate ? (
          <button
            onClick={() => onAction(ext.pkgName, 'update')}
            disabled={inProgress}
            className="p-2.5 bg-blue-600/10 hover:bg-blue-600 border border-blue-600/20 text-blue-400 hover:text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-md hover:scale-[1.03]"
            title="Mettre à jour l'extension"
          >
            {inProgress ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <ArrowUpCircle className="w-4 h-4" />
                <span className="hidden sm:inline text-[9px] uppercase tracking-wider font-black">MàJ</span>
              </>
            )}
          </button>
        ) : ext.isInstalled ? (
          <button
            onClick={() => onAction(ext.pkgName, 'uninstall')}
            disabled={inProgress}
            className="p-2.5 bg-red-600/10 hover:bg-red-600 border border-red-600/20 text-red-400 hover:text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-md hover:scale-[1.03]"
            title="Désinstaller l'extension"
          >
            {inProgress ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Trash2 className="w-4 h-4" />
                <span className="hidden sm:inline text-[9px] uppercase tracking-wider font-black">Suppr.</span>
              </>
            )}
          </button>
        ) : (
          <button
            onClick={() => onAction(ext.pkgName, 'install')}
            disabled={inProgress}
            className="p-2.5 bg-green-600/10 hover:bg-green-600 border border-green-600/20 text-green-400 hover:text-white rounded-xl text-xs font-bold transition-all disabled:opacity-50 flex items-center gap-1.5 shadow-md hover:scale-[1.03]"
            title="Installer l'extension"
          >
            {inProgress ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Download className="w-4 h-4" />
                <span className="hidden sm:inline text-[9px] uppercase tracking-wider font-black">Instal.</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export const ExtensionRow = React.memo(ExtensionRowComponent);
