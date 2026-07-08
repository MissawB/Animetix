import React, { useState, useEffect } from 'react';
import { getOpenDatasets, downloadDataset } from '../../api';
import { OpenDataset } from '../../types';
import { Card } from '../../components/ui/Card';
import { Share2, Download, FileText, Database, Loader2, ExternalLink } from 'lucide-react';
import { useToastStore } from '../../store/toastStore';
import { useTranslation } from 'react-i18next';

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

const OpenDataPage: React.FC = () => {
  const [datasets, setDatasets] = useState<OpenDataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const addToast = useToastStore((state) => state.addToast);
  const { t } = useTranslation();

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const response = await getOpenDatasets();
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
      await downloadDataset(dataset.id, originalFilename);
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
      <div className="p-20 text-center text-white font-black animate-pulse uppercase tracking-[0.3em] flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-brand-primary" />
        {t('social.opendata.loading', 'Synchronisation avec le dépôt open-source...')}
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="mb-12">
        <h1 className="text-4xl font-black italic manga-font tracking-tighter uppercase flex items-center gap-3">
          <Share2 className="w-8 h-8 text-teal-400 animate-pulse" />{' '}
          {t('social.opendata.title', 'PORTAIL DE DONNÉES OUVERTES')}
        </h1>
        <p className="text-xs text-gray-400 font-bold uppercase tracking-wider mt-2">
          {t(
            'social.opendata.subtitle',
            'Nos jeux de données publics — en téléchargement direct ou sur Hugging Face.',
          )}
        </p>
      </div>

      {/* Téléchargement direct */}
      <h2 className="text-xs font-black uppercase tracking-[0.25em] text-teal-400 mb-4">
        {t('social.opendata.direct_download', 'Téléchargement direct')}
      </h2>

      {/* Dataset Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {datasets.map((dataset) => (
          <Card
            key={dataset.id}
            padding="lg"
            className="flex flex-col justify-between hover:border-teal-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-teal-950/10 group relative overflow-hidden"
          >
            {/* Background Accent */}
            <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/5 rounded-bl-full pointer-events-none group-hover:bg-teal-500/10 transition-colors" />

            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-teal-500/10 text-teal-400 group-hover:scale-110 transition-transform">
                  {dataset.id === 'dpo_pairs' ? (
                    <Database className="w-6 h-6" />
                  ) : (
                    <FileText className="w-6 h-6" />
                  )}
                </div>
                <div>
                  <h4 className="font-black text-md uppercase tracking-tight text-white group-hover:text-teal-400 transition-colors">
                    {dataset.name}
                  </h4>
                  <span className="text-[9px] font-black uppercase text-gray-500 tracking-wider bg-white/5 dark:bg-black/20 px-2 py-0.5 rounded">
                    {t('social.opendata.format', 'Format')} {dataset.format}
                  </span>
                </div>
              </div>

              <p className="text-xs text-gray-400 leading-relaxed font-medium">
                {dataset.description}
              </p>

              {/* Metadata list */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5 text-[10px] font-black uppercase tracking-wider text-gray-500">
                <div>
                  <span className="block text-[8px] opacity-40">
                    {t('social.opendata.file_size', 'Taille du fichier')}
                  </span>
                  <span className="text-white">{formatBytes(dataset.size_bytes)}</span>
                </div>
                <div>
                  <span className="block text-[8px] opacity-40">
                    {t('social.opendata.last_update', 'Dernière mise à jour')}
                  </span>
                  <span className="text-white">{formatDate(dataset.updated_at)}</span>
                </div>
              </div>
            </div>

            <div className="pt-6 mt-6 border-t border-white/5">
              <button
                onClick={() => handleDownload(dataset)}
                disabled={downloadingId !== null}
                className="w-full inline-flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-black font-black uppercase text-xs tracking-widest py-3 px-6 rounded-xl transition-all duration-300 shadow-md disabled:opacity-50 disabled:cursor-not-allowed group-hover:scale-[1.02]"
              >
                {downloadingId === dataset.id ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-black" />
                    {t('social.opendata.preparing', 'Préparation...')}
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 text-black group-hover:translate-y-0.5 transition-transform" />
                    {t('social.opendata.download_btn', 'Télécharger le dataset')}
                  </>
                )}
              </button>
            </div>
          </Card>
        ))}

        {datasets.length === 0 && (
          <Card
            padding="lg"
            className="col-span-full text-center py-20 border-dashed border-2 border-white/5"
          >
            <Database className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="font-bold text-gray-500 italic">
              {t('social.opendata.empty', 'Aucun dataset en téléchargement direct pour le moment.')}
            </p>
          </Card>
        )}
      </div>

      {/* Sur Hugging Face */}
      <h2 className="text-xs font-black uppercase tracking-[0.25em] text-teal-400 mt-14 mb-4">
        {t('social.opendata.on_hf', 'Sur Hugging Face')}
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {HF_DATASETS.map((ds) => (
          <a
            key={ds.url}
            href={ds.url}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={t('social.opendata.aria_label', '{{name}} — voir sur Hugging Face', {
              name: ds.name,
            })}
            className="no-underline group"
          >
            <Card
              padding="lg"
              className="h-full flex flex-col justify-between hover:border-teal-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-teal-950/10 relative overflow-hidden"
            >
              <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/5 rounded-bl-full pointer-events-none group-hover:bg-teal-500/10 transition-colors" />
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-teal-500/10 text-teal-400 group-hover:scale-110 transition-transform">
                    <Database className="w-6 h-6" />
                  </div>
                  <div>
                    <h4 className="font-black text-md uppercase tracking-tight text-white group-hover:text-teal-400 transition-colors">
                      {ds.name}
                    </h4>
                    <span className="text-[9px] font-black uppercase text-gray-500 tracking-wider bg-white/5 dark:bg-black/20 px-2 py-0.5 rounded">
                      {ds.tag}
                    </span>
                  </div>
                </div>
                <p className="text-xs text-gray-400 leading-relaxed font-medium">
                  {t(ds.descriptionKey, ds.descriptionDefault)}
                </p>
              </div>
              <div className="pt-6 mt-6 border-t border-white/5">
                <span className="w-full inline-flex items-center justify-center gap-2 border border-teal-500/30 text-teal-400 group-hover:bg-teal-500/10 font-black uppercase text-xs tracking-widest py-3 px-6 rounded-xl transition-all duration-300">
                  <ExternalLink className="w-4 h-4" />
                  {t('social.opendata.view_hf', 'Voir sur Hugging Face')}
                </span>
              </div>
            </Card>
          </a>
        ))}
      </div>
    </div>
  );
};

export default OpenDataPage;
