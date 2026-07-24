import React, { useState, useEffect } from 'react';
import { labService } from '../../features/labs/services/labService';
import { OpenDataset } from '../../types';
import { Download, Database, Loader2, ExternalLink } from 'lucide-react';
import { useToastStore } from '../../store/toastStore';
import { useTranslation } from 'react-i18next';
import { LabPage, LabHeader } from '../labs/components/shared/LabKit';

/** Encre du module Open Data (la donnée) — or. */
const DATA_INK = '#FDB913';

// Jeux de données publiés sur le Hub Hugging Face (consultables / téléchargeables
// directement là-bas).
const HF_DATASETS = [
  {
    name: 'Otaku Expert Dataset',
    descriptionKey: 'social.opendata.hf_expert_desc',
    descriptionDefault:
      "Jeu de données d'entraînement (SFT) expert pour les modèles de raisonnement Otaku, rédigé en français.",
    tag: 'Text Generation · FR · ~10K–100K',
    url: 'https://huggingface.co/datasets/MissawB/otaku-expert-dataset',
  },
  {
    name: 'Otaku Gold Dataset',
    descriptionKey: 'social.opendata.hf_gold_desc',
    descriptionDefault:
      "Jeu de données étalon (vérité terrain) pour évaluer la précision des modèles, l'extraction d'entités et les pipelines RAG.",
    tag: 'Question Answering · < 1K',
    url: 'https://huggingface.co/datasets/MissawB/otaku-gold-dataset',
  },
];

/** Titre de section à barre d'encre or (voix données). */
const SectionTitle: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div className={`mb-6 flex items-center gap-3 ${className}`}>
    <span className="h-4 w-1 flex-none bg-[#FDB913]" aria-hidden />
    <h2 className="font-manga text-sm font-black uppercase italic tracking-wide text-[#F4F1E8]">
      {children}
    </h2>
    <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
  </div>
);

const OpenDataPage: React.FC = () => {
  const [datasets, setDatasets] = useState<OpenDataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const addToast = useToastStore((state) => state.addToast);
  const { t } = useTranslation();

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const response = await labService.getOpenDatasets();
        if (response.status === 'success') {
          setDatasets(response.datasets);
        }
      } catch (err) {
        console.error('Erreur lors de la récupération des datasets :', err);
        addToast(
          t('social.opendata.load_error', 'Impossible de charger les métadonnées des datasets.'),
          'error',
        );
      } finally {
        setIsLoading(false);
      }
    };
    fetchDatasets().then();
  }, [addToast, t]);

  const handleDownload = async (dataset: OpenDataset) => {
    setDownloadingId(dataset.id);
    const originalFilename =
      dataset.id === 'dpo_pairs' ? 'dpo_train_validated.jsonl' : 'gameplay_sessions.jsonl';
    try {
      addToast(
        t('social.opendata.downloading', 'Téléchargement de {{name}} en cours...', {
          name: dataset.name,
        }),
        'info',
      );
      await labService.downloadDataset(dataset.id, originalFilename);
      addToast(
        t('social.opendata.download_success', '{{name}} téléchargé avec succès !', {
          name: dataset.name,
        }),
        'success',
      );
    } catch (err) {
      console.error(`Erreur lors du téléchargement de ${dataset.id} :`, err);
      addToast(
        t('social.opendata.download_fail', 'Échec du téléchargement de {{name}}.', {
          name: dataset.name,
        }),
        'error',
      );
    } finally {
      setDownloadingId(null);
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Octet';
    const k = 1024;
    const sizes = ['Octets', 'Ko', 'Mo', 'Go'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateStr: string): string => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen w-full flex-col items-center justify-center gap-4 bg-[#0B0C10] text-center">
        <Loader2 className="h-10 w-10 animate-spin text-[#FDB913]" aria-hidden="true" />
        <p className="animate-pulse text-xs font-black uppercase tracking-[0.3em] text-[#8F94A5]">
          {t('social.opendata.loading', 'Synchronisation avec le dépôt open-source...')}
        </p>
      </div>
    );
  }

  return (
    <LabPage>
      <LabHeader
        glyph="開"
        code="Registre · Open Data"
        title="Portail"
        accent="Open Data"
        lede={t(
          'social.opendata.subtitle',
          'Nos jeux de données publics — en téléchargement direct ou sur Hugging Face.',
        )}
      />

      {/* Téléchargement direct */}
      <SectionTitle>{t('social.opendata.direct_download', 'Téléchargement direct')}</SectionTitle>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {datasets.map((dataset) => (
          <article
            key={dataset.id}
            className="group relative flex flex-col justify-between overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 transition-all duration-300 hover:-translate-y-1 hover:border-[#FDB913]/60"
          >
            <span
              aria-hidden
              className="pointer-events-none absolute -bottom-5 -right-2 select-none text-[5.5rem] font-black leading-none text-[#F4F1E8]/[0.045] transition-colors duration-500 group-hover:text-[#FDB913]/[0.08]"
            >
              開
            </span>

            <div className="relative space-y-4">
              <div className="flex items-start justify-between gap-3">
                <span
                  className="select-none text-2xl font-bold leading-none"
                  style={{ color: DATA_INK }}
                  aria-hidden
                >
                  開
                </span>
                <span className="rounded bg-[#F4F1E8]/5 px-2 py-0.5 text-[9px] font-black uppercase tracking-wider text-[#8F94A5]">
                  {t('social.opendata.format', 'Format')} {dataset.format}
                </span>
              </div>

              <h4 className="font-manga text-lg font-black uppercase italic tracking-tight text-[#F4F1E8]">
                {dataset.name}
              </h4>
              <p className="text-xs leading-relaxed text-[#8F94A5]">{dataset.description}</p>

              {/* Métadonnées */}
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] px-4 py-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.2em] text-[#8F94A5]">
                    {t('social.opendata.file_size', 'Taille du fichier')}
                  </p>
                  <p className="mt-1 text-xs font-black uppercase text-[#F4F1E8]">
                    {formatBytes(dataset.size_bytes)}
                  </p>
                </div>
                <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] px-4 py-3">
                  <p className="text-[9px] font-black uppercase tracking-[0.2em] text-[#8F94A5]">
                    {t('social.opendata.last_update', 'Dernière mise à jour')}
                  </p>
                  <p className="mt-1 text-xs font-black uppercase text-[#F4F1E8]">
                    {formatDate(dataset.updated_at)}
                  </p>
                </div>
              </div>
            </div>

            <div className="relative mt-6 border-t border-[#F4F1E8]/10 pt-6">
              <button
                onClick={() => handleDownload(dataset)}
                disabled={downloadingId !== null}
                className="inline-flex w-full cursor-pointer items-center justify-center gap-2 rounded-xl border-none bg-[#FDB913] px-6 py-3.5 text-xs font-black uppercase tracking-widest text-[#0B0C10] transition-colors hover:bg-[#e0a60e] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#F4F1E8]"
              >
                {downloadingId === dataset.id ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    {t('social.opendata.preparing', 'Préparation...')}
                  </>
                ) : (
                  <>
                    <Download className="h-4 w-4" aria-hidden="true" />
                    {t('social.opendata.download_btn', 'Télécharger le dataset')}
                  </>
                )}
              </button>
            </div>
          </article>
        ))}

        {datasets.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center rounded-2xl border border-dashed border-[#F4F1E8]/15 px-8 py-20 text-center">
            <Database className="mb-4 h-12 w-12 text-[#8F94A5]/40" aria-hidden="true" />
            <p className="text-sm italic text-[#8F94A5]">
              {t('social.opendata.empty', 'Aucun dataset en téléchargement direct pour le moment.')}
            </p>
          </div>
        )}
      </div>

      {/* Sur Hugging Face */}
      <SectionTitle className="mt-14">
        {t('social.opendata.on_hf', 'Sur Hugging Face')}
      </SectionTitle>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {HF_DATASETS.map((ds) => (
          <a
            key={ds.url}
            href={ds.url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={t('social.opendata.aria_label', '{{name}} — voir sur Hugging Face', {
              name: ds.name,
            })}
            className="group block h-full no-underline"
          >
            <article className="flex h-full flex-col justify-between rounded-2xl border border-[#F4F1E8]/15 p-6 transition-colors duration-300 group-hover:border-[#FDB913]">
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <span
                    className="select-none text-2xl font-bold leading-none opacity-70"
                    style={{ color: DATA_INK }}
                    aria-hidden
                  >
                    開
                  </span>
                  <span className="rounded bg-[#F4F1E8]/5 px-2 py-0.5 text-[9px] font-black uppercase tracking-wider text-[#8F94A5]">
                    {ds.tag}
                  </span>
                </div>
                <h4 className="font-manga text-lg font-black uppercase italic tracking-tight text-[#F4F1E8] transition-colors group-hover:text-[#FDB913]">
                  {ds.name}
                </h4>
                <p className="text-xs leading-relaxed text-[#8F94A5]">
                  {t(ds.descriptionKey, ds.descriptionDefault)}
                </p>
              </div>
              <div className="mt-6 border-t border-[#F4F1E8]/10 pt-6">
                <span className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-[#F4F1E8]/15 px-5 py-2.5 text-xs font-black uppercase tracking-widest text-[#8F94A5] transition-colors group-hover:border-[#FDB913] group-hover:text-[#F4F1E8]">
                  <ExternalLink className="h-4 w-4" aria-hidden="true" />
                  {t('social.opendata.view_hf', 'Voir sur Hugging Face')}
                </span>
              </div>
            </article>
          </a>
        ))}
      </div>
    </LabPage>
  );
};

export default OpenDataPage;
