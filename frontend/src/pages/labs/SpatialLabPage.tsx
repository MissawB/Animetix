import React, { useState, Suspense } from 'react';
import { Layers, Wand2, ArrowRight, Image as ImageIcon, Box, Cuboid, Sparkles } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { useTranslation } from 'react-i18next';

import { Link } from 'react-router-dom';

// three.js (~590 KB) is pulled in only by GLBViewer, which itself renders only
// after the user generates a 3D model. Lazy-load it so three ships in an async
// chunk fetched when the viewer actually mounts, instead of on every visit to
// this page.
const GLBViewer = React.lazy(() => import('../../components/three/GLBViewer'));

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
        headers: {},
      });
    },
    onSuccess: (data) => {
      setDepthResult(data);
    },
  });

  const model3dMutation = useMutation({
    mutationFn: async () => {
      if (!image && !imageFile) return;
      const formData = new FormData();
      if (imageFile) formData.append('image_file', imageFile);
      else if (image) formData.append('image_url', image);
      formData.append('mode', 'mesh'); // 'gaussian_splatting' is also supported via WebGL, but the GLB viewer renders mesh output

      return apiClient('/api/v1/spatial-lab/generate-3d/', {
        method: 'POST',
        body: formData,
        headers: {},
      });
    },
    onSuccess: (data) => {
      setModelResult(data);
    },
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
              <Layers className="w-4 h-4" /> {t('labs.spatial.analyzer_title', 'Analyseur 3D')}
            </h3>

            <Button
              onClick={() => document.getElementById('spatial-upload')?.click()}
              variant="outline"
              fullWidth
              className="mb-4 bg-black text-white hover:bg-gray-900 border-none"
            >
              {t('labs.spatial.choose_image', 'CHOISIR UNE IMAGE')}
            </Button>
            <input
              type="file"
              id="spatial-upload"
              aria-label={t('labs.spatial.choose_image', 'Choisir une image')}
              className="hidden"
              accept="image/*"
              onChange={handleUpload}
            />

            <div className="space-y-3">
              <Button
                onClick={() => depthMutation.mutate()}
                disabled={!image || isLoading}
                variant="primary"
                fullWidth
              >
                <Wand2 className="w-5 h-5" /> {t('labs.spatial.est_depth', 'EST. PROFONDEUR')}
              </Button>

              <Button
                onClick={() => model3dMutation.mutate()}
                disabled={!image || isLoading}
                variant="secondary"
                fullWidth
                className="bg-purple-600 hover:bg-purple-700 text-white border-none py-6"
              >
                <Cuboid className="w-5 h-5" />{' '}
                {t('labs.spatial.generate_3d_btn', 'GÉNÉRER MODÈLE 3D')}
              </Button>
            </div>
          </Card>

          <Card padding="lg" className="bg-gray-900 text-white/40 border-white/5">
            <Box className="w-12 h-12 mb-4 opacity-10" />
            <p className="text-xs font-bold leading-relaxed italic mb-4">
              {t(
                'labs.spatial.desc1',
                "Reconstruisez la géométrie 3D à partir d'une image 2D grâce aux modèles monoculaires.",
              )}
            </p>
            <p className="text-xs font-bold leading-relaxed italic text-purple-400">
              {t(
                'labs.spatial.desc2',
                'NEW: La "Génération Modèle 3D" utilise l\'IA Gaussian Splatting pour créer un objet complet manipulable.',
              )}
            </p>
            <Button
              as={Link}
              to="/lab/spatial/gallery/"
              variant="outline"
              fullWidth
              className="mt-4 border-blue-500/30 text-blue-400 hover:bg-blue-500/10 text-[10px] font-black uppercase tracking-widest"
            >
              {t('labs.spatial.view_gallery', 'VOIR MA GALERIE 3D')}{' '}
              <ArrowRight className="ml-2 w-3 h-3" />
            </Button>

            <Button
              as={Link}
              to="/cinematic-reconstruction/"
              variant="outline"
              fullWidth
              className="mt-4 border-purple-500/30 text-purple-400 hover:bg-purple-500/10 text-[10px] font-black uppercase tracking-widest"
            >
              {t('labs.spatial.discover_dcs', 'DÉCOUVRIR LE DCS (3D VIDÉO)')}{' '}
              <ArrowRight className="ml-2 w-3 h-3" />
            </Button>
          </Card>
        </div>

        {/* Viewport */}
        <div className="lg:col-span-3">
          <div className="bg-black rounded-[4rem] shadow-2xl overflow-hidden min-h-[600px] relative border-4 border-white/5 flex items-center justify-center p-8">
            {isLoading && (
              <div className="absolute inset-0 bg-black/80 backdrop-blur-sm z-50 flex flex-col items-center justify-center">
                <div className="w-20 h-20 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6 shadow-[0_0_20px_rgba(59,130,246,0.5)]"></div>
                <span className="text-white font-black italic uppercase tracking-[0.3em] animate-pulse">
                  {model3dMutation.isPending
                    ? t(
                        'labs.spatial.generating_3d',
                        'Génération 3D en cours (peut prendre ~15s)...',
                      )
                    : t('labs.spatial.analyzing_depth', 'Analyse IA Profondeur...')}
                </span>
              </div>
            )}

            {!image ? (
              <div className="text-center opacity-10 animate-pulse">
                <ImageIcon className="w-40 h-40 mx-auto mb-6" />
                <span className="text-2xl font-black italic manga-font uppercase">
                  {t('labs.spatial.no_source', 'Aucune source chargée')}
                </span>
              </div>
            ) : (
              <div
                className={`grid ${modelResult ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2'} gap-8 w-full h-full animate-fade-in`}
              >
                {!modelResult && (
                  <div className="space-y-4">
                    <Badge variant="neutral" className="bg-white/10 text-white border-white/10">
                      Original
                    </Badge>
                    <img
                      src={image}
                      className="w-full rounded-2xl shadow-2xl border border-white/10"
                      alt="Original"
                      loading="lazy"
                      decoding="async"
                    />
                  </div>
                )}

                {modelResult ? (
                  <div className="space-y-4 w-full h-[600px] flex flex-col items-center">
                    <Badge variant="primary" className="bg-purple-600">
                      {t('labs.spatial.interactive_model', 'Modèle 3D Interactif ({{format}})', {
                        format: modelResult.format,
                      })}
                    </Badge>
                    <div className="w-full h-full relative rounded-2xl overflow-hidden border border-white/10 bg-gray-900/50">
                      <Suspense
                        fallback={
                          <div className="w-full h-full flex items-center justify-center">
                            <div className="w-10 h-10 border-4 border-purple-500 border-t-transparent rounded-full animate-spin" />
                          </div>
                        }
                      >
                        <GLBViewer
                          src={modelResult.model_url}
                          autoRotate
                          style={{ width: '100%', height: '100%' }}
                        />
                      </Suspense>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Badge variant="primary">Profondeur (IA)</Badge>
                    {depthResult ? (
                      <img
                        src={depthResult.depth_map}
                        className="w-full rounded-2xl shadow-2xl border border-white/10"
                        alt="Depth Map"
                        loading="lazy"
                        decoding="async"
                      />
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

      {/* Guide & Protocole */}
      <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card
          padding="lg"
          className="bg-white dark:bg-black/40 border-blue-500/20 shadow-[0_0_50px_rgba(59,130,246,0.1)] relative overflow-hidden group"
        >
          <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
            <Layers className="w-64 h-64 text-blue-500" />
          </div>
          <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
            <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400" />{' '}
            {t('labs.spatial.guide_title', 'Guide Spatial')}
          </h4>
          <div className="space-y-4 relative z-10">
            <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
              <span className="text-blue-600 dark:text-blue-400">
                {t('labs.spatial.guide_source_title', "L'Image Source :")}
              </span>{' '}
              {t(
                'labs.spatial.guide_source_desc',
                "Chargez n'importe quelle image 2D (personnage, décor, objet). C'est le point de départ de toute l'analyse.",
              )}
            </p>
            <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
              <span className="text-blue-600 dark:text-blue-400">
                {t('labs.spatial.guide_depth_title', 'La Profondeur :')}
              </span>{' '}
              {t(
                'labs.spatial.guide_depth_desc',
                "L'IA estime la distance de chaque pixel et produit une carte de profondeur, comme si elle voyait le relief de l'image.",
              )}
            </p>
            <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
              <span className="text-blue-600 dark:text-blue-400">
                {t('labs.spatial.guide_model_title', 'Le Modèle 3D :')}
              </span>{' '}
              {t(
                'labs.spatial.guide_model_desc',
                "En un clic, l'image devient un objet 3D complet que vous pouvez faire tourner à la souris et retrouver dans votre galerie.",
              )}
            </p>
          </div>
        </Card>

        <div className="p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-black/5 dark:border-white/5 flex flex-col justify-center text-center">
          <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-blue-800/70 dark:text-blue-200/60">
            {t(
              'labs.spatial.guide_footer_1',
              "Estimation de profondeur monoculaire et reconstruction 3D (maillage GLB, Gaussian Splatting) à partir d'une seule image.",
            )}{' '}
            <br />
            {t(
              'labs.spatial.guide_footer_2',
              'Le modèle généré est rendu dans un viewer WebGL interactif et archivé dans la galerie 3D.',
            )}
          </p>
        </div>
      </div>
    </div>
  );
};

export default SpatialLabPage;
