import React, { useState } from 'react';
import { Upload, CheckCircle, Loader2 } from 'lucide-react';
import { apiClient } from '../../utils/apiClient';
import { useToastStore } from '../../store/toastStore';

export const VideoIndexing: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [videoId, setVideoId] = useState('');
  const [isIndexing, setIsIndexing] = useState(false);
  const { addToast } = useToastStore();

  const handleUpload = async () => {
    if (!file || !videoId) return;

    setIsIndexing(true);
    const formData = new FormData();
    formData.append('video', file);
    formData.append('video_id', videoId);

    try {
      const response = await apiClient('/api/v1/labs/video/index/', {
        method: 'POST',
        body: formData,
        isFormData: true,
      });

      if (response.status === 'success') {
        addToast(`Vidéo indexée avec succès ! ${response.indexed_segments} segments créés.`, 'success');
        setFile(null);
        setVideoId('');
      } else {
        addToast(response.error || "Erreur lors de l'indexation", 'error');
      }
    } catch (error: any) {
      console.error('Indexing error:', error);
      // Erreur déjà gérée par apiClient globalement, mais on peut ajouter un log spécifique
    } finally {
      setIsIndexing(false);
    }
  };

  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 space-y-6">
      <div className="flex items-center gap-3 border-b border-white/5 pb-4">
        <Upload className="w-5 h-5 text-red-500" />
        <h2 className="text-sm font-black uppercase tracking-widest text-white">Indexation Master (Admin)</h2>
      </div>

      <div className="space-y-4">
        <div>
          <label className="text-[10px] font-black uppercase opacity-40 tracking-widest block mb-2">ID Unique du Média</label>
          <input
            type="text"
            value={videoId}
            onChange={(e) => setVideoId(e.target.value)}
            placeholder="ex: OP_1_NARUTO"
            className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-2 text-sm focus:border-red-500 outline-none transition-all"
          />
        </div>

        <div>
          <label className="text-[10px] font-black uppercase opacity-40 tracking-widest block mb-2">Fichier Vidéo (.mp4, .mkv)</label>
          <div className="relative group">
            <input
              type="file"
              accept="video/*"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="w-full text-xs text-white/60 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-black file:bg-red-500/20 file:text-red-500 hover:file:bg-red-500/30 cursor-pointer"
            />
          </div>
        </div>

        <button
          onClick={handleUpload}
          disabled={isIndexing || !file || !videoId}
          className="w-full py-3 bg-red-600 hover:bg-red-700 disabled:opacity-30 disabled:cursor-not-allowed text-white font-black italic uppercase text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
        >
          {isIndexing ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" /> Indexation en cours...
            </>
          ) : (
            <>
              <CheckCircle className="w-4 h-4" /> Lancer l'analyse VLM
            </>
          )}
        </button>
      </div>
      
      <p className="text-[9px] text-white/30 italic leading-relaxed">
        Note: L'indexation peut prendre plusieurs minutes car elle nécessite l'exécution de modèles de vision (Qwen2-VL) sur chaque image clé. 
        Le serveur traitera la vidéo segment par segment.
      </p>
    </div>
  );
};
