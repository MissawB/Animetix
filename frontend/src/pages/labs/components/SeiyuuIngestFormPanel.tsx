import React from 'react';
import { Loader2, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { LabPanel, LAB_INPUT, LAB_LABEL, LAB_BTN_GHOST } from './shared/LabKit';

/** Action principale compacte (même voix que LAB_CTA, sans w-full). */
const CTA_COMPACT =
  'inline-flex cursor-pointer items-center justify-center gap-2 rounded-xl border-none bg-[#E8442B] px-8 py-3 font-manga text-sm font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50';

interface SeiyuuIngestFormPanelProps {
  ingestName: string;
  setIngestName: (val: string) => void;
  ingestLang: string;
  setIngestLang: (val: string) => void;
  ingestSource: string;
  setIngestSource: (val: string) => void;
  ingestDef: string;
  setIngestDef: (val: string) => void;
  ingestRoles: string;
  setIngestRoles: (val: string) => void;
  ingestError: string;
  ingestSuccess: string;
  isPending: boolean;
  onCancel: () => void;
  onSubmit: (e: React.FormEvent) => void;
}

export const SeiyuuIngestFormPanel: React.FC<SeiyuuIngestFormPanelProps> = ({
  ingestName,
  setIngestName,
  ingestLang,
  setIngestLang,
  ingestSource,
  setIngestSource,
  ingestDef,
  setIngestDef,
  ingestRoles,
  setIngestRoles,
  ingestError,
  ingestSuccess,
  isPending,
  onCancel,
  onSubmit,
}) => {
  const { t } = useTranslation();

  return (
    <motion.div
      initial={{ height: 0, opacity: 0 }}
      animate={{ height: 'auto', opacity: 1 }}
      exit={{ height: 0, opacity: 0 }}
      className="mb-12 overflow-hidden"
    >
      <LabPanel
        title={t('labs.seiyuu.ingest_title', 'Ingestion et extraction vocale')}
        corner="30 Bx"
      >
        <p className="mb-6 text-xs leading-relaxed text-[#8F94A5]">
          {t('labs.seiyuu.ingest_cost_label', 'Coût :')}{' '}
          <span className="font-black text-[#FDB913]">30 Bx</span>{' '}
          {t(
            'labs.seiyuu.ingest_cost_desc',
            "— L'IA télécharge l'audio, isole les fréquences vocales (80Hz - 8000Hz) et découpe un échantillon de 10s sans silence.",
          )}
        </p>

        <form onSubmit={onSubmit} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="ingest-name" className={LAB_LABEL}>
                {t('labs.seiyuu.ingest_name_label', 'Nom du Doubleur / Seiyuu')}
              </label>
              <input
                id="ingest-name"
                aria-label="Nom du doubleur ou seiyuu"
                type="text"
                value={ingestName}
                onChange={(e) => setIngestName(e.target.value)}
                placeholder="Ex: Donald Reignoux, Rie Takahashi"
                className={LAB_INPUT}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="ingest-lang" className={LAB_LABEL}>
                {t('labs.seiyuu.ingest_lang_label', 'Langue / Spécialisation')}
              </label>
              <select
                id="ingest-lang"
                value={ingestLang}
                onChange={(e) => setIngestLang(e.target.value)}
                className={LAB_INPUT}
              >
                <option value="japanese">
                  {t('labs.seiyuu.lang_option_ja', 'Japonais (Seiyuu)')}
                </option>
                <option value="french">
                  {t('labs.seiyuu.lang_option_fr', 'Français (Doubleur)')}
                </option>
                <option value="other">{t('labs.seiyuu.lang_option_other', 'Autre')}</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="ingest-source" className={LAB_LABEL}>
              {t('labs.seiyuu.ingest_source_label', 'URL YouTube ou requête de recherche')}
            </label>
            <input
              id="ingest-source"
              aria-label="URL YouTube ou requête de recherche"
              type="text"
              value={ingestSource}
              onChange={(e) => setIngestSource(e.target.value)}
              placeholder="Ex: https://www.youtube.com/watch?v=... ou 'Donald Reignoux Titeuf interview'"
              className={LAB_INPUT}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="space-y-2">
              <label htmlFor="ingest-def" className={LAB_LABEL}>
                {t('labs.seiyuu.ingest_def_label', 'Définition / Description (optionnel)')}
              </label>
              <textarea
                id="ingest-def"
                aria-label="Définition ou description du doubleur"
                value={ingestDef}
                onChange={(e) => setIngestDef(e.target.value)}
                placeholder="Ex: Acteur français à voix claire, connu pour doubler Sora..."
                className={`${LAB_INPUT} h-24 resize-none`}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="ingest-roles" className={LAB_LABEL}>
                {t(
                  'labs.seiyuu.ingest_roles_label',
                  'Rôles emblématiques (séparés par des virgules)',
                )}
              </label>
              <textarea
                id="ingest-roles"
                aria-label="Rôles emblématiques (séparés par des virgules)"
                value={ingestRoles}
                onChange={(e) => setIngestRoles(e.target.value)}
                placeholder="Ex: Sora, Spider-Man, Titeuf, Reese"
                className={`${LAB_INPUT} h-24 resize-none`}
              />
            </div>
          </div>

          {ingestError && (
            <div className="rounded-xl border border-[#E8442B]/30 bg-[#E8442B]/10 p-4 text-xs font-bold text-[#E8442B]">
              {ingestError}
            </div>
          )}

          {ingestSuccess && (
            <div className="flex items-center gap-2 rounded-xl border border-[#FDB913]/30 bg-[#FDB913]/10 p-4 text-xs font-black text-[#FDB913]">
              <Sparkles className="h-4 w-4 flex-none" aria-hidden="true" /> {ingestSuccess}
            </div>
          )}

          <div className="flex justify-end gap-4 pt-2">
            <button type="button" className={LAB_BTN_GHOST} onClick={onCancel}>
              {t('common.cancel', 'Annuler')}
            </button>
            <button type="submit" disabled={isPending} className={CTA_COMPACT}>
              {isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />{' '}
                  {t('labs.seiyuu.ingestion_in_progress', 'Ingestion en cours...')}
                </>
              ) : (
                t('labs.seiyuu.start_ingestion', "Lancer l'ingestion")
              )}
            </button>
          </div>
        </form>
      </LabPanel>
    </motion.div>
  );
};
