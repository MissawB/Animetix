import React from 'react';
import { Check, Share2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export const ShareButton: React.FC<{ title: string }> = ({ title }) => {
  const { t } = useTranslation();
  const [copied, setCopied] = React.useState(false);

  const share = async () => {
    const url = window.location.href;
    if (navigator.share) {
      try {
        await navigator.share({ title, url });
        return;
      } catch {
        // annulé par l'utilisateur — rien à faire
        return;
      }
    }
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // presse-papier indisponible (contexte non sécurisé / API absente) — rien à faire
    }
  };

  return (
    <button
      onClick={share}
      aria-label={t('media.detail.share', 'Partager')}
      className="inline-flex items-center gap-2 px-3.5 py-2.5 bg-white/5 border border-white/10 text-white rounded-lg cursor-pointer"
    >
      {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Share2 className="w-4 h-4" />}
      {copied && (
        <span className="text-[10px] font-black uppercase tracking-widest">
          {t('media.detail.link_copied', 'Lien copié')}
        </span>
      )}
    </button>
  );
};
