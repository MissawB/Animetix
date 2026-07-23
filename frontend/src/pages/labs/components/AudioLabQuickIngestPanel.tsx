import React from 'react';
import { Video, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { useQuickIngestForm } from '../../../features/labs/hooks/useQuickIngestForm';
import { LAB_INPUT, LAB_BTN_GHOST } from './shared/LabKit';

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
          className="space-y-4 overflow-hidden rounded-2xl border border-[#F4F1E8]/15 bg-[#0F1016] p-5"
        >
          <h4 className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
            <Video className="h-3.5 w-3.5 text-[#E8442B]" aria-hidden="true" />{' '}
            {t('labs.audio.ingest_title', 'Ajouter via YouTube (30 Bx)')}
          </h4>
          <div className="space-y-1">
            <input
              type="text"
              placeholder={t('labs.audio.ingest_actor_name', "Nom de l'acteur")}
              aria-label={t('labs.audio.ingest_actor_name', "Nom de l'acteur")}
              value={quickIngest.name}
              onChange={(e) => quickIngest.setName(e.target.value)}
              className={LAB_INPUT}
            />
          </div>
          <div className="space-y-1">
            <select
              value={quickIngest.language}
              onChange={(e) => quickIngest.setLanguage(e.target.value)}
              className={LAB_INPUT}
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
              className={LAB_INPUT}
            />
          </div>
          {quickIngest.error && (
            <p className="text-[10px] font-bold text-[#E8442B]">{quickIngest.error}</p>
          )}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={quickIngest.close}
              className={`${LAB_BTN_GHOST} text-[10px]`}
            >
              {t('labs.audio.ingest_cancel', 'Annuler')}
            </button>
            <button
              type="submit"
              disabled={isIngestingVoice}
              className="inline-flex cursor-pointer items-center gap-2 rounded-full border-none bg-[#E8442B] px-5 py-2.5 text-[10px] font-black uppercase tracking-widest text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isIngestingVoice ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                t('labs.audio.ingest_submit', 'Ingérer')
              )}
            </button>
          </div>
        </motion.form>
      )}
    </AnimatePresence>
  );
};
