import React from 'react';
import { Loader2, Download, Trash2, ArrowUpCircle } from 'lucide-react';
import type { Extension, ExtensionAction } from '../types';
import { useAuthStore } from '../../../../store/authStore';

interface ExtensionRowProps {
  ext: Extension;
  onAction: (pkgName: string, action: ExtensionAction) => void;
  inProgress: boolean;
  getProxiedImageUrl: (url: string) => string;
}

const ExtensionRowComponent: React.FC<ExtensionRowProps> = ({
  ext,
  onAction,
  inProgress,
  getProxiedImageUrl,
}) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  // Gérer une extension mute le serveur → réservé aux utilisateurs connectés.
  const disabled = inProgress || !isAuthenticated;
  const lockTitle = !isAuthenticated ? 'Connexion requise pour gérer les extensions' : undefined;

  // Bouton d'action, coloré selon l'action (palette édition de nuit) :
  // installer = or (kin), MàJ = indigo (ai), désinstaller = vermillon (shu).
  const actionBtn = (tone: 'gold' | 'indigo' | 'shu') => {
    const tones = {
      gold: 'border-[#FDB913]/25 bg-[#FDB913]/10 text-[#FDB913] hover:bg-[#FDB913] hover:text-[#0B0C10]',
      indigo:
        'border-[#5D7FD3]/25 bg-[#5D7FD3]/10 text-[#5D7FD3] hover:bg-[#5D7FD3] hover:text-[#0B0C10]',
      shu: 'border-[#E8442B]/25 bg-[#E8442B]/10 text-[#E8442B] hover:bg-[#E8442B] hover:text-[#F4F1E8]',
    } as const;
    return `flex items-center gap-1.5 rounded-xl border px-2.5 py-2.5 text-xs font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${tones[tone]}`;
  };

  return (
    <div className="group flex items-center gap-4 rounded-2xl border border-[#F4F1E8]/5 bg-[#0F1016] p-4 transition-colors hover:border-[#F4F1E8]/15">
      {/* Icône */}
      {/* onError est un repli d'image (événement média), pas une interaction utilisateur. */}
      {/* eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions */}
      <img
        src={getProxiedImageUrl(ext.iconUrl)}
        alt={ext.name}
        className="h-10 w-10 flex-shrink-0 rounded-xl border border-[#F4F1E8]/5 bg-[#F4F1E8]/5 object-contain p-1"
        onError={(e) => {
          e.currentTarget.src = 'https://via.placeholder.com/150?text=Manga';
        }}
        loading="lazy"
        decoding="async"
      />

      {/* Infos */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <h4 className="line-clamp-1 text-sm font-bold text-[#F4F1E8]/90 transition-colors group-hover:text-[#FDB913]">
            {ext.name}
          </h4>
          <span className="rounded-full bg-[#F4F1E8]/5 px-2 py-0.5 text-[8px] font-black uppercase tracking-wider text-[#8F94A5]">
            {ext.lang}
          </span>
        </div>
        <p className="mt-0.5 truncate text-[10px] font-medium tabular-nums text-[#8F94A5]">
          v{ext.versionName}
        </p>

        <div className="mt-1.5 flex gap-1.5">
          {ext.isNsfw && (
            <span className="rounded border border-[#E8442B]/20 bg-[#E8442B]/10 px-1.5 py-0.5 text-[7px] font-black uppercase tracking-widest text-[#E8442B]">
              18+
            </span>
          )}
          {ext.isObsolete && (
            <span className="rounded border border-[#FDB913]/20 bg-[#FDB913]/10 px-1.5 py-0.5 text-[7px] font-black uppercase tracking-widest text-[#FDB913]">
              Obsolète
            </span>
          )}
        </div>
      </div>

      {/* Action */}
      <div className="flex-shrink-0">
        {ext.hasUpdate ? (
          <button
            type="button"
            onClick={() => onAction(ext.pkgName, 'update')}
            disabled={disabled}
            className={actionBtn('indigo')}
            title={lockTitle ?? "Mettre à jour l'extension"}
          >
            {inProgress ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <ArrowUpCircle className="h-4 w-4" />
                <span className="hidden text-[9px] font-black uppercase tracking-wider sm:inline">
                  MàJ
                </span>
              </>
            )}
          </button>
        ) : ext.isInstalled ? (
          <button
            type="button"
            onClick={() => onAction(ext.pkgName, 'uninstall')}
            disabled={disabled}
            className={actionBtn('shu')}
            title={lockTitle ?? "Désinstaller l'extension"}
          >
            {inProgress ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Trash2 className="h-4 w-4" />
                <span className="hidden text-[9px] font-black uppercase tracking-wider sm:inline">
                  Suppr.
                </span>
              </>
            )}
          </button>
        ) : (
          <button
            type="button"
            onClick={() => onAction(ext.pkgName, 'install')}
            disabled={disabled}
            className={actionBtn('gold')}
            title={lockTitle ?? "Installer l'extension"}
          >
            {inProgress ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                <Download className="h-4 w-4" />
                <span className="hidden text-[9px] font-black uppercase tracking-wider sm:inline">
                  Instal.
                </span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export const ExtensionRow = React.memo(ExtensionRowComponent);
