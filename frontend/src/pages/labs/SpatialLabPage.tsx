import React, { useState, Suspense } from 'react';
import { Wand2, ArrowRight, Image as ImageIcon, Cuboid, Upload } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { useTranslation } from 'react-i18next';

import { Link } from 'react-router-dom';

import {
  LabPage,
  LabHeader,
  LabPanel,
  LabGuide,
  LAB_CTA,
  LAB_BTN_GHOST,
} from './components/shared/LabKit';

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
    <LabPage>
      <LabHeader
        code="Protocole · Spatial"
        title="Relief"
        accent="monoculaire"
        lede="Charge une image 2D : le lab estime la distance de chaque pixel pour en tirer une carte de profondeur, puis reconstruit un objet 3D complet, manipulable dans un viewer WebGL."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-4">
        {/* Instruments */}
        <div className="space-y-8 lg:col-span-1">
          <LabPanel title={t('labs.spatial.analyzer_title', 'Analyseur 3D')}>
            <div className="space-y-3">
              <button
                type="button"
                onClick={() => document.getElementById('spatial-upload')?.click()}
                className={`${LAB_BTN_GHOST} w-full justify-center`}
              >
                <Upload className="h-3.5 w-3.5" aria-hidden="true" />{' '}
                {t('labs.spatial.choose_image', 'CHOISIR UNE IMAGE')}
              </button>
              <input
                type="file"
                id="spatial-upload"
                aria-label={t('labs.spatial.choose_image', 'Choisir une image')}
                className="hidden"
                accept="image/*"
                onChange={handleUpload}
              />

              <button
                type="button"
                onClick={() => depthMutation.mutate()}
                disabled={!image || isLoading}
                className={LAB_CTA}
              >
                <Wand2 className="h-5 w-5" aria-hidden="true" />{' '}
                {t('labs.spatial.est_depth', 'EST. PROFONDEUR')}
              </button>

              <button
                type="button"
                onClick={() => model3dMutation.mutate()}
                disabled={!image || isLoading}
                className={`${LAB_CTA} bg-transparent text-[#FDB913] hover:bg-[#FDB913]/10 border border-solid border-[#FDB913]/40`}
              >
                <Cuboid className="h-5 w-5" aria-hidden="true" />{' '}
                {t('labs.spatial.generate_3d_btn', 'GÉNÉRER MODÈLE 3D')}
              </button>
            </div>
          </LabPanel>

          <LabPanel title="Notes de terrain">
            <p className="text-sm leading-relaxed text-[#8F94A5]">
              {t(
                'labs.spatial.desc1',
                "Reconstruisez la géométrie 3D à partir d'une image 2D grâce aux modèles monoculaires.",
              )}
            </p>
            <p className="mt-4 text-sm leading-relaxed text-[#FDB913]">
              {t(
                'labs.spatial.desc2',
                'NEW: La "Génération Modèle 3D" utilise l\'IA Gaussian Splatting pour créer un objet complet manipulable.',
              )}
            </p>
            <div className="mt-6 space-y-3">
              <Link to="/lab/spatial/gallery/" className={`${LAB_BTN_GHOST} w-full justify-center`}>
                {t('labs.spatial.view_gallery', 'VOIR MA GALERIE 3D')}{' '}
                <ArrowRight className="h-3 w-3" aria-hidden="true" />
              </Link>

              <Link
                to="/cinematic-reconstruction/"
                className={`${LAB_BTN_GHOST} w-full justify-center`}
              >
                {t('labs.spatial.discover_dcs', 'DÉCOUVRIR LE DCS (3D VIDÉO)')}{' '}
                <ArrowRight className="h-3 w-3" aria-hidden="true" />
              </Link>
            </div>
          </LabPanel>
        </div>

        {/* Viewport */}
        <div className="lg:col-span-3">
          <div className="relative flex min-h-[600px] items-center justify-center overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8">
            {isLoading && (
              <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-[#0B0C10]/85 backdrop-blur-sm">
                <div className="mb-6 h-16 w-16 animate-spin rounded-full border-4 border-[#FDB913]/20 border-t-[#FDB913]" />
                <span className="text-xs font-black uppercase tracking-[0.3em] text-[#F4F1E8]">
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
              <div className="text-center">
                <ImageIcon
                  className="mx-auto mb-6 h-32 w-32 text-[#8F94A5]/25"
                  aria-hidden="true"
                />
                <span className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]/60">
                  {t('labs.spatial.no_source', 'Aucune source chargée')}
                </span>
                <p className="mt-3 text-sm text-[#8F94A5]">
                  Choisis une image dans le panneau de gauche pour démarrer l'analyse.
                </p>
              </div>
            ) : (
              <div
                className={`grid ${modelResult ? 'grid-cols-1' : 'grid-cols-1 md:grid-cols-2'} h-full w-full gap-8 animate-fade-in`}
              >
                {!modelResult && (
                  <div className="space-y-4">
                    <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                      Original
                    </span>
                    <img
                      src={image}
                      className="w-full rounded-xl border border-[#F4F1E8]/10"
                      alt="Original"
                      loading="lazy"
                      decoding="async"
                    />
                  </div>
                )}

                {modelResult ? (
                  <div className="flex h-[600px] w-full flex-col items-center space-y-4">
                    <span className="text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                      {t('labs.spatial.interactive_model', 'Modèle 3D Interactif ({{format}})', {
                        format: modelResult.format,
                      })}
                    </span>
                    <div className="relative h-full w-full overflow-hidden rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]">
                      <Suspense
                        fallback={
                          <div className="flex h-full w-full items-center justify-center">
                            <div className="h-10 w-10 animate-spin rounded-full border-4 border-[#FDB913]/20 border-t-[#FDB913]" />
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
                    <span className="text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                      Profondeur (IA)
                    </span>
                    {depthResult ? (
                      <img
                        src={depthResult.depth_map}
                        className="w-full rounded-xl border border-[#F4F1E8]/10"
                        alt="Depth Map"
                        loading="lazy"
                        decoding="async"
                      />
                    ) : (
                      <div className="flex aspect-square w-full items-center justify-center rounded-xl border border-dashed border-[#F4F1E8]/15 bg-[#0B0C10]">
                        <ArrowRight className="h-12 w-12 text-[#8F94A5]/40" aria-hidden="true" />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: "L'image source",
            body: t(
              'labs.spatial.guide_source_desc',
              "Chargez n'importe quelle image 2D (personnage, décor, objet). C'est le point de départ de toute l'analyse.",
            ),
          },
          {
            title: 'La profondeur',
            body: t(
              'labs.spatial.guide_depth_desc',
              "L'IA estime la distance de chaque pixel et produit une carte de profondeur, comme si elle voyait le relief de l'image.",
            ),
          },
          {
            title: 'Le modèle 3D',
            body: t(
              'labs.spatial.guide_model_desc',
              "En un clic, l'image devient un objet 3D complet que vous pouvez faire tourner à la souris et retrouver dans votre galerie.",
            ),
          },
        ]}
        note={`${t(
          'labs.spatial.guide_footer_1',
          "Estimation de profondeur monoculaire et reconstruction 3D (maillage GLB, Gaussian Splatting) à partir d'une seule image.",
        )} ${t(
          'labs.spatial.guide_footer_2',
          'Le modèle généré est rendu dans un viewer WebGL interactif et archivé dans la galerie 3D.',
        )}`}
      />
    </LabPage>
  );
};

export default SpatialLabPage;
