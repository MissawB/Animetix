import React from 'react';
import { Video, Loader2, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';

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
      className="overflow-hidden mb-12"
    >
      <Card
        padding="lg"
        className="bg-[#12121e]/80 border border-emerald-500/20 backdrop-blur-xl rounded-[2.5rem] p-8"
      >
        <h3 className="text-2xl font-black italic uppercase manga-font flex items-center gap-3 mb-6 text-emerald-400">
          <Video className="w-6 h-6 text-red-500" />{' '}
          {t('labs.seiyuu.ingest_title', 'Ingestion et extraction vocale')}
        </h3>
        <p className="text-xs font-bold opacity-50 uppercase tracking-widest mb-6">
          {t('labs.seiyuu.ingest_cost_label', 'Coût :')}{' '}
          <span className="text-emerald-400">30 Bx</span>{' '}
          {t(
            'labs.seiyuu.ingest_cost_desc',
            "— L'IA télécharge l'audio, isole les fréquences vocales (80Hz - 8000Hz) et découpe un échantillon de 10s sans silence.",
          )}
        </p>

        <form onSubmit={onSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label
                htmlFor="ingest-name"
                className="text-[10px] font-black uppercase tracking-wider opacity-60"
              >
                {t('labs.seiyuu.ingest_name_label', 'Nom du Doubleur / Seiyuu')}
              </label>
              <input
                id="ingest-name"
                aria-label="Nom du doubleur ou seiyuu"
                type="text"
                value={ingestName}
                onChange={(e) => setIngestName(e.target.value)}
                placeholder="Ex: Donald Reignoux, Rie Takahashi"
                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50"
              />
            </div>
            <div className="space-y-2">
              <label
                htmlFor="ingest-lang"
                className="text-[10px] font-black uppercase tracking-wider opacity-60"
              >
                {t('labs.seiyuu.ingest_lang_label', 'Langue / Spécialisation')}
              </label>
              <select
                id="ingest-lang"
                value={ingestLang}
                onChange={(e) => setIngestLang(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50 text-white"
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
            <label
              htmlFor="ingest-source"
              className="text-[10px] font-black uppercase tracking-wider opacity-60"
            >
              {t('labs.seiyuu.ingest_source_label', 'URL YouTube ou requête de recherche')}
            </label>
            <input
              id="ingest-source"
              aria-label="URL YouTube ou requête de recherche"
              type="text"
              value={ingestSource}
              onChange={(e) => setIngestSource(e.target.value)}
              placeholder="Ex: https://www.youtube.com/watch?v=... ou 'Donald Reignoux Titeuf interview'"
              className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label
                htmlFor="ingest-def"
                className="text-[10px] font-black uppercase tracking-wider opacity-60"
              >
                {t('labs.seiyuu.ingest_def_label', 'Définition / Description (optionnel)')}
              </label>
              <textarea
                id="ingest-def"
                aria-label="Définition ou description du doubleur"
                value={ingestDef}
                onChange={(e) => setIngestDef(e.target.value)}
                placeholder="Ex: Acteur français à voix claire, connu pour doubler Sora..."
                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50 h-24 resize-none"
              />
            </div>
            <div className="space-y-2">
              <label
                htmlFor="ingest-roles"
                className="text-[10px] font-black uppercase tracking-wider opacity-60"
              >
                {t('labs.seiyuu.ingest_roles_label', 'Iconic Roles (séparés par des virgules)')}
              </label>
              <textarea
                id="ingest-roles"
                aria-label="Rôles emblématiques (séparés par des virgules)"
                value={ingestRoles}
                onChange={(e) => setIngestRoles(e.target.value)}
                placeholder="Ex: Sora, Spider-Man, Titeuf, Reese"
                className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 font-bold text-sm outline-none focus:border-emerald-500/50 h-24 resize-none"
              />
            </div>
          </div>

          {ingestError && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 text-red-400 font-bold rounded-xl text-xs">
              ⚠️ {ingestError}
            </div>
          )}

          {ingestSuccess && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-black rounded-xl text-xs flex items-center gap-2 animate-pulse">
              <Sparkles className="w-4 h-4 text-glow" /> {ingestSuccess}
            </div>
          )}

          <div className="flex justify-end gap-4 pt-2">
            <Button type="button" variant="ghost" onClick={onCancel}>
              {t('common.cancel', 'Annuler')}
            </Button>
            <Button
              type="submit"
              disabled={isPending}
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-black italic uppercase px-8 py-3 rounded-xl flex items-center gap-2 border-none"
            >
              {isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />{' '}
                  {t('labs.seiyuu.ingestion_in_progress', 'Ingestion en cours...')}
                </>
              ) : (
                t('labs.seiyuu.start_ingestion', "Lancer l'ingestion")
              )}
            </Button>
          </div>
        </form>
      </Card>
    </motion.div>
  );
};
