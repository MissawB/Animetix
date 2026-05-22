import React, { useState } from 'react';
import { Layers, Wand2, ArrowRight, Image as ImageIcon, Box } from 'lucide-react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';

import { useTranslation } from 'react-i18next';

interface SpatialResult {
  original: string;
  depth_map: string;
  status: string;
}

const SpatialLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [image, setImage] = useState<string | null>(null);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [result, setResult] = useState<SpatialResult | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
        if (!image && !imageFile) return;
        const formData = new FormData();
        if (imageFile) formData.append('image_file', imageFile);
        else if (image) formData.append('image_url', image);

        return apiClient('/api/v1/spatial-lab/', {
            method: 'POST',
            body: formData,
            headers: {} // Laisse le navigateur gérer le Content-Type pour FormData
        });
    },
    onSuccess: (data) => {
        setResult(data);
    }
  });

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      setImage(URL.createObjectURL(file));
      setResult(null);
    }
  };

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
                  <input type="file" id="spatial-upload" className="hidden" onChange={handleUpload} />

                  <Button 
                      onClick={() => mutation.mutate()}
                      disabled={!image || mutation.isPending}
                      variant="primary"
                      fullWidth
                  >
                      <Wand2 className="w-5 h-5" /> GÉNÉRER PROFONDEUR
                  </Button>
              </Card>

              <Card padding="lg" className="bg-gray-900 text-white/40 border-white/5">
                  <Box className="w-12 h-12 mb-4 opacity-10" />
                  <p className="text-xs font-bold leading-relaxed italic">
                      Cet outil utilise des modèles d'estimation de profondeur monoculaire pour reconstruire la géométrie 3D à partir d'une simple image 2D.
                  </p>
              </Card>
          </div>

          {/* Viewport */}
          <div className="lg:col-span-3">
              <div className="bg-black rounded-[4rem] shadow-2xl overflow-hidden min-h-[600px] relative border-4 border-white/5 flex items-center justify-center p-8">
                  {mutation.isPending && (
                      <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
                          <div className="w-20 h-20 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6 shadow-[0_0_20px_rgba(59,130,246,0.5)]"></div>
                          <span className="text-white font-black italic uppercase tracking-[0.3em] animate-pulse">IA Reconstruction...</span>
                      </div>
                  )}

                  {!image ? (
                      <div className="text-center opacity-10 animate-pulse">
                          <ImageIcon className="w-40 h-40 mx-auto mb-6" />
                          <span className="text-2xl font-black italic manga-font uppercase">Aucune source chargée</span>
                      </div>
                  ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full h-full animate-fade-in">
                          <div className="space-y-4">
                              <Badge variant="neutral" className="bg-white/10 text-white border-white/10">Original</Badge>
                              <img src={image} className="w-full rounded-2xl shadow-2xl border border-white/10" alt="Original" />
                          </div>
                          <div className="space-y-4">
                              <Badge variant="primary">Profondeur (IA)</Badge>
                              {result ? (
                                  <img src={result.depth_map} className="w-full rounded-2xl shadow-2xl border border-white/10" alt="Depth Map" />
                              ) : (
                                  <div className="w-full aspect-square bg-white/5 rounded-2xl flex items-center justify-center border border-white/5 border-dashed">
                                      <ArrowRight className="w-12 h-12 text-white opacity-10" />
                                  </div>
                              )}
                          </div>
                      </div>
                  )}
              </div>
          </div>
        </div>
      </div>
    
  );
};

export default SpatialLabPage;
