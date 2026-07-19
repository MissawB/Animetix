import React from 'react';
import { Video, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../../../components/ui/Button';
import { useQuickIngestForm } from '../../../features/labs/hooks/useQuickIngestForm';

type QuickIngestForm = ReturnType<typeof useQuickIngestForm>;

/** Collapsible "add a voice from YouTube" form in the sidebar. Pure view over
 *  the `useQuickIngestForm` state object owned by the parent. */
export const AudioLabQuickIngestPanel: React.FC<{
  quickIngest: QuickIngestForm;
  isIngestingVoice: boolean;
}> = ({ quickIngest, isIngestingVoice }) => {
  const { t } = useTranslation();
  return (
    <AnimatePresence>
      {quickIngest.isOpen && (
        <motion.form
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          onSubmit={quickIngest.submit}
          className="bg-navy-950/80 border border-blue-500/20 p-5 rounded-2xl space-y-4 overflow-hidden"
        >
          <h4 className="text-[10px] font-black uppercase tracking-widest text-blue-400 flex items-center gap-1">
            <Video className="w-3.5 h-3.5 text-red-500" />{' '}
            {t('labs.audio.ingest_title', 'Ajouter via YouTube (30 Bx)')}
          </h4>
          <div className="space-y-1">
            <input
              type="text"
              placeholder={t('labs.audio.ingest_actor_name', "Nom de l'acteur")}
              aria-label={t('labs.audio.ingest_actor_name', "Nom de l'acteur")}
              value={quickIngest.name}
              onChange={(e) => quickIngest.setName(e.target.value)}
              className="w-full bg-black/45 border border-white/5 rounded-lg px-3 py-2 text-xs font-bold text-white"
            />
          </div>
          <div className="space-y-1">
            <select
              value={quickIngest.language}
              onChange={(e) => quickIngest.setLanguage(e.target.value)}
              className="w-full bg-black/45 border border-white/5 rounded-lg px-3 py-2 text-xs font-bold text-white"
            >
              <option value="japanese">
                {t('labs.audio.ingest_lang_japanese', 'Japonais (Seiyuu)')}
              </option>
              <option value="french">
                {t('labs.audio.ingest_lang_french', 'Français (Doubleur)')}
              </option>
            </select>
          </div>
          <div className="space-y-1">
            <input
              type="text"
              placeholder={t('labs.audio.ingest_source_placeholder', 'Lien YouTube ou recherche')}
              aria-label={t('labs.audio.ingest_source_placeholder', 'Lien YouTube ou recherche')}
              value={quickIngest.source}
              onChange={(e) => quickIngest.setSource(e.target.value)}
              className="w-full bg-black/45 border border-white/5 rounded-lg px-3 py-2 text-xs font-bold text-white"
            />
          </div>
          {quickIngest.error && (
            <p className="text-[9px] font-bold text-red-400">⚠️ {quickIngest.error}</p>
          )}
          <div className="flex gap-2 justify-end">
            <Button type="button" size="sm" variant="ghost" onClick={quickIngest.close}>
              {t('labs.audio.ingest_cancel', 'Annuler')}
            </Button>
            <Button
              type="submit"
              size="sm"
              className="bg-blue-600 hover:bg-blue-500 border-none"
              disabled={isIngestingVoice}
            >
              {isIngestingVoice ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                t('labs.audio.ingest_submit', 'Ingérer')
              )}
            </Button>
          </div>
        </motion.form>
      )}
    </AnimatePresence>
  );
};
