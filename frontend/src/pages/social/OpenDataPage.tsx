import React, { useState, useEffect } from 'react';
import { getOpenDatasets, downloadDataset } from '../../api';
import { OpenDataset } from '../../types';
import { Card } from "../../components/ui/Card";
import { Share2, Download, FileText, Database, Info, Loader2 } from 'lucide-react';
import { useToastStore } from '../../store/toastStore';

const OpenDataPage: React.FC = () => {
  const [datasets, setDatasets] = useState<OpenDataset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const addToast = useToastStore((state) => state.addToast);

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const response = await getOpenDatasets();
        if (response.status === 'success') {
          setDatasets(response.datasets);
        }
      } catch (err) {
        console.error("Erreur lors de la récupération des datasets :", err);
        addToast("Impossible de charger les métadonnées des datasets.", "error");
      } finally {
        setIsLoading(false);
      }
    };
    fetchDatasets().then();
  }, [addToast]);

  const handleDownload = async (dataset: OpenDataset) => {
    setDownloadingId(dataset.id);
    const originalFilename = dataset.id === 'dpo_pairs' ? 'dpo_train_validated.jsonl' : 'gameplay_sessions.jsonl';
    try {
      addToast(`Téléchargement de ${dataset.name} en cours...`, "info");
      await downloadDataset(dataset.id, originalFilename);
      addToast(`${dataset.name} téléchargé avec succès !`, "success");
    } catch (err) {
      console.error(`Erreur lors du téléchargement de ${dataset.id} :`, err);
      addToast(`Échec du téléchargement de ${dataset.name}.`, "error");
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
        minute: '2-digit'
      });
    } catch (e) {
      return dateStr;
    }
  };

  if (isLoading) {
    return (
      <div className="p-20 text-center text-white font-black animate-pulse uppercase tracking-[0.3em] flex flex-col items-center justify-center gap-4">
        <Loader2 className="w-10 h-10 animate-spin text-brand-primary" />
        Synchronisation avec le dépôt open-source...
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-12 gap-6">
        <div>
          <h1 className="text-4xl font-black italic manga-font tracking-tighter uppercase flex items-center gap-3">
            <Share2 className="w-8 h-8 text-teal-400 animate-pulse" /> PORTAIL DE DONNÉES OUVERTES
          </h1>
          <p className="text-xs text-gray-400 font-bold uppercase tracking-wider mt-2">
            Transparence, science ouverte et conformité académique pour l'intelligence artificielle.
          </p>
        </div>
        <div className="bg-teal-500/10 border border-teal-500/20 px-4 py-3 rounded-2xl flex items-center gap-3 shrink-0">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping" />
          <span className="text-[10px] font-black uppercase text-teal-400 tracking-wider">Conformité RGPD & Éthique</span>
        </div>
      </div>

      {/* Info Card */}
      <Card padding="lg" className="mb-10 bg-gradient-to-br from-teal-950/20 via-navy-950/20 to-transparent border-teal-500/10">
        <div className="flex gap-4">
          <Info className="w-8 h-8 text-teal-400 shrink-0" />
          <div className="space-y-2">
            <h3 className="font-black text-sm uppercase tracking-wider text-teal-400">Pourquoi partageons-nous ces données ?</h3>
            <p className="text-xs text-gray-300 leading-relaxed font-bold">
              Conformément aux exigences de reproductibilité scientifique et aux standards éthiques de l'IA (notamment l'EU AI Act), nous rendons publics nos jeux de données d'apprentissage par renforcement (RLHF/DPO) ainsi que les traces d'interaction anonymisées.
            </p>
            <p className="text-[10px] text-gray-500 font-medium">
              *Toutes les données ont subi un processus d'anonymisation strict (suppression des identifiants directs, hashing cryptographique et masquage différentiel) pour protéger la vie privée de notre communauté.
            </p>
          </div>
        </div>
      </Card>

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
                  {dataset.id === 'dpo_pairs' ? <Database className="w-6 h-6" /> : <FileText className="w-6 h-6" />}
                </div>
                <div>
                  <h4 className="font-black text-md uppercase tracking-tight text-white group-hover:text-teal-400 transition-colors">
                    {dataset.name}
                  </h4>
                  <span className="text-[9px] font-black uppercase text-gray-500 tracking-wider bg-white/5 dark:bg-black/20 px-2 py-0.5 rounded">
                    Format {dataset.format}
                  </span>
                </div>
              </div>

              <p className="text-xs text-gray-400 leading-relaxed font-medium">
                {dataset.description}
              </p>

              {/* Metadata list */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5 text-[10px] font-black uppercase tracking-wider text-gray-500">
                <div>
                  <span className="block text-[8px] opacity-40">Taille du fichier</span>
                  <span className="text-white">{formatBytes(dataset.size_bytes)}</span>
                </div>
                <div>
                  <span className="block text-[8px] opacity-40">Dernière mise à jour</span>
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
                    Préparation...
                  </>
                ) : (
                  <>
                    <Download className="w-4 h-4 text-black group-hover:translate-y-0.5 transition-transform" />
                    Télécharger le dataset
                  </>
                )}
              </button>
            </div>
          </Card>
        ))}

        {datasets.length === 0 && (
          <Card padding="lg" className="col-span-full text-center py-20 border-dashed border-2 border-white/5">
            <Database className="w-12 h-12 text-gray-600 mx-auto mb-4" />
            <p className="font-bold text-gray-500 italic">Aucun dataset public n'est actuellement disponible.</p>
            <p className="text-xs text-gray-400 mt-2 uppercase tracking-widest">Les pipelines d'anonymisation sont en cours d'exécution.</p>
          </Card>
        )}
      </div>
    </div>
  );
};

export default OpenDataPage;
