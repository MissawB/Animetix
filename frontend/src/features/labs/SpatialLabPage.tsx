import React, { useState } from 'react';
import { Layers, Wand2, ArrowRight, Image as ImageIcon, Box, Cuboid } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { useTranslation } from 'react-i18next';
import '@google/model-viewer';

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': React.DetailedHTMLProps<React.HTMLAttributes<HTMLElement> & {
        src?: string;
        alt?: string;
        'auto-rotate'?: boolean;
        'camera-controls'?: boolean;
        style?: React.CSSProperties;
      }, HTMLElement>;
    }
  }
}

interface SpatialResult {
  original?: string;
  depth_map?: string;
  status: string;
}

interface Model3DResult {
  status: string;
  task_id: string;
  mode: string;
  model_url: string;
  preview_video: string | null;
  polycount: string | number;
  format: string;
}

const SpatialLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [image, setImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [depthResult, setDepthResult] = useState<SpatialResult | null>(null);
  const [modelResult, setModelResult] = useState<Model3DResult | null>(null);

  const depthMutation = useMutation({
    mutationFn: async () => {
        if (!image && !imageFile) return;
        const formData = new FormData();
        if (imageFile) formData.append('image_file', imageFile);
        else if (image) formData.append('image_url', image);

        return apiClient('/api/v1/spatial-lab/', {
            method: 'POST',
            body: formData,
            headers: {}
        });
    },
    onSuccess: (data) => {
        setDepthResult(data);
    }
  });

  const model3dMutation = useMutation({
    mutationFn: async () => {
        if (!image && !imageFile) return;
        const formData = new FormData();
        if (imageFile) formData.append('image_file', imageFile);
        else if (image) formData.append('image_url', image);
        formData.append('mode', 'mesh'); // 'gaussian_splatting' is also supported if viewing via WebGL, but model-viewer uses GLB

        return apiClient('/api/v1/spatial-lab/generate-3d/', {
            method: 'POST',
            body: formData,
            headers: {}
        });
    },
    onSuccess: (data) => {
        setModelResult(data);
    }
  });

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      setImage(URL.createObjectURL(file));
      setDepthResult(null);
      setModelResult(null);
    }
  };

  const isLoading = depthMutation.isPending || model3dMutation.isPending;

  return (
      <div className="max-w-7xl mx-auto px-6 py-16">
        <h1 className="text-6xl font-black italic manga-font mb-12 tracking-tighter uppercase text-center md:text-left">
          SPATIAL <span className="text-blue-500">LAB</span>
        </h1>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
          {/* Controls */}
          <div className="lg:col-span-1 space-y-8">
              <Card padding="lg" className="h-fit">
                  <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                      <Layers className="w-4 h-4" /> Analyseur 3D
                  </h3>
                  
                  <Button 
                      onClick={() => document.getElementById('spatial-upload')?.click()}
                      variant="outline"
                      fullWidth
                      className="mb-4 bg-black text-white hover:bg-gray-900 border-none"
                  >
                      CHOISIR UNE IMAGE
                  </Button>
                  <input type="file" id="spatial-upload" className="hidden" accept="image/*" onChange={handleUpload} />

                  <div className="space-y-3">
                      <Button 
                          onClick={() => depthMutation.mutate()}
                          disabled={!image || isLoading}
                          variant="primary"
                          fullWidth
                      >
                          <Wand2 className="w-5 h-5" /> EST. PROFONDEUR
                      </Button>
                      
                      <Button 
                          onClick={() => model3dMutation.mutate()}
                          disabled={!image || isLoading}
                          variant="secondary"
                          fullWidth
                          className="bg-purple-600 hover:bg-purple-700 text-white border-none"
                      >
                          <Cuboid className="w-5 h-5" /> GÉNÉRER MODÈLE 3D
                      </Button>
                  </div>
              </Card>

              <Card padding="lg" className="bg-gray-900 text-white/40 border-white/5">
                  <Box className="w-12 h-12 mb-4 opacity-10" />
                  <p className="text-xs font-bold leading-relaxed italic mb-4">
                      Reconstruisez la géométrie 3D à partir d'une image 2D grâce aux modèles monoculaires.
                  </p>
                  <p className="text-xs font-bold leading-relaxed italic text-purple-400">
                      NEW: La "Génération Modèle 3D" utilise l'IA Gaussian Splatting pour créer un objet complet manipulable.
                  </p>
              </Card>
          </div>

          {/* Viewport */}
          <div className="lg:col-span-3">
              <div className="bg-black rounded-[4rem] shadow-2xl overflow-hidden min-h-[600px] relative border-4 border-white/5 flex items-center justify-center p-8">
                  {isLoading && (
                      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
                          <div className="w-20 h-20 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6 shadow-[0_0_20px_rgba(59,130,246,0.5)]"></div>
                          <span className="text-white font-black italic uppercase tracking-[0.3em] animate-pulse">
                              {model3dMutation.isPending ? "Génération 3D en cours (peut prendre ~15s)..." : "Analyse IA Profondeur..."}
                          </span>
                      </div>
                  )}

                  {!image ? (
                      <div className="text-center opacity-10 animate-pulse">
                          <ImageIcon className="w-40 h-40 mx-auto mb-6" />
                          <span className="text-2xl font-black italic manga-font uppercase">Aucune source chargée</span>
                      </div>
                  ) : (
                      <div className={`grid ${modelResult ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2'} gap-8 w-full h-full animate-fade-in`}>
                          {!modelResult && (
                              <div className="space-y-4">
                                  <Badge variant="neutral" className="bg-white/10 text-white border-white/10">Original</Badge>
                                  <img src={image} className="w-full rounded-2xl shadow-2xl border border-white/10" alt="Original" />
                              </div>
                          )}

                          {modelResult ? (
                              <div className="space-y-4 w-full h-[600px] flex flex-col items-center">
                                  <Badge variant="primary" className="bg-purple-600">Modèle 3D Interactif ({modelResult.format})</Badge>
                                  <div className="w-full h-full relative rounded-2xl overflow-hidden border border-white/10 bg-gray-900/50">
                                      <model-viewer
                                          src={modelResult.model_url}
                                          alt="Generated 3D Model"
                                          auto-rotate
                                          camera-controls
                                          style={{ width: '100%', height: '100%' }}
                                      ></model-viewer>
                                  </div>
                              </div>
                          ) : (
                              <div className="space-y-4">
                                  <Badge variant="primary">Profondeur (IA)</Badge>
                                  {depthResult ? (
                                      <img src={depthResult.depth_map} className="w-full rounded-2xl shadow-2xl border border-white/10" alt="Depth Map" />
                                  ) : (
                                      <div className="w-full aspect-square bg-white/5 rounded-2xl flex items-center justify-center border border-white/5 border-dashed">
                                          <ArrowRight className="w-12 h-12 text-white opacity-10" />
                                      </div>
                                  )}
                              </div>
                          )}
                      </div>
                  )}
              </div>
          </div>
        </div>
      </div>
  );
};

export default SpatialLabPage;
