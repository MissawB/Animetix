import React from 'react';
import { useTranslation } from 'react-i18next';
import { Wrench, RefreshCw, Clock } from 'lucide-react';

interface MaintenancePageProps {
  message?: string | null;
  until?: string | null;
  onRetry?: () => void;
}

/**
 * Page plein écran affichée aux visiteurs quand le mode maintenance est actif.
 * Rendue HORS du Layout (pas de navbar/footer) : elle porte son propre fond
 * sombre forcé (data-bs-theme), comme les pages volontairement sombres du site.
 */
const MaintenancePage: React.FC<MaintenancePageProps> = ({ message, until, onRetry }) => {
  const { t, i18n } = useTranslation();

  const untilLabel = React.useMemo(() => {
    if (!until) return null;
    const date = new Date(until);
    if (Number.isNaN(date.getTime())) return null;
    return date.toLocaleString(i18n.language?.startsWith('en') ? 'en-GB' : 'fr-FR', {
      day: 'numeric',
      month: 'long',
      hour: '2-digit',
      minute: '2-digit',
    });
  }, [until, i18n.language]);

  return (
    <div
      data-bs-theme="dark"
      className="min-h-screen bg-[#05050a] text-white flex items-center justify-center px-6 relative overflow-hidden"
    >
      {/* Aura d'ambiance */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-yellow-400/5 blur-[120px] rounded-full animate-pulse pointer-events-none" />

      <div className="text-center space-y-8 max-w-xl relative z-10">
        {/* Icône lumineuse */}
        <div className="relative inline-block">
          <div className="absolute -inset-8 bg-yellow-400/10 rounded-full blur-3xl animate-pulse" />
          <div className="relative w-32 h-32 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-[2rem] flex items-center justify-center -rotate-12 shadow-2xl mx-auto">
            <Wrench className="w-16 h-16 text-black" />
          </div>
        </div>

        <div>
          <h1 className="text-[9rem] leading-none font-black italic manga-font tracking-tighter text-transparent bg-clip-text bg-gradient-to-b from-white/20 to-white/5 select-none">
            503
          </h1>
        </div>

        <div className="space-y-3">
          <h2 className="text-3xl font-black italic manga-font uppercase tracking-tight">
            {t('maintenance.title_1', 'Maintenance')}{' '}
            <span className="text-yellow-400 text-glow">
              {t('maintenance.title_2', 'en cours')}
            </span>
          </h2>
          <p className="text-sm font-bold text-gray-400 uppercase tracking-[0.2em] max-w-md mx-auto leading-relaxed">
            {message?.trim()
              ? message
              : t(
                  'maintenance.default_desc',
                  'Animetix fait une pause technique pour revenir plus fort. Merci de votre patience !',
                )}
          </p>
          {untilLabel && (
            <p className="inline-flex items-center gap-2 text-[11px] font-black uppercase tracking-widest text-yellow-400/90 bg-yellow-400/10 border border-yellow-400/20 rounded-full px-4 py-2 mt-2">
              <Clock className="w-3.5 h-3.5" />
              {t('maintenance.eta', { defaultValue: 'Retour estimé : {{date}}', date: untilLabel })}
            </p>
          )}
        </div>

        {onRetry && (
          <div className="pt-4">
            <button
              onClick={onRetry}
              className="inline-flex items-center gap-2 bg-yellow-400 hover:bg-yellow-300 text-black py-4 px-8 rounded-2xl shadow-xl hover:scale-105 transition-all font-black uppercase italic tracking-wider"
            >
              <RefreshCw className="w-5 h-5" /> {t('maintenance.retry', 'Réessayer')}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MaintenancePage;
