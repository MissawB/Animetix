import React, { useState } from 'react';
import { Box, Video, Zap, Play, Loader2, ChevronRight, Target, Maximize2 } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { apiClient } from '../../utils/apiClient';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_LABEL,
  LAB_CTA,
} from './components/shared/LabKit';

interface DCSFrame {
  model_url: string;
  timestamp: number;
  point_count: number;
}

interface DCSResult {
  frames: DCSFrame[];
}

const CinematicReconstructionPage: React.FC = () => {
  const { t } = useTranslation();
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [reconstructionResult, setReconstructionResult] = useState<DCSResult | null>(null);

  const mutation = useMutation<DCSResult, Error, FormData>({
    mutationFn: (formData: FormData) =>
      apiClient('/api/v1/spatial-lab/cinematic-reconstruction/', {
        method: 'POST',
        body: formData,
        isFormData: true,
      }),
    onSuccess: (data) => {
      setReconstructionResult(data);
    },
  });

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      const url = URL.createObjectURL(file);
      setVideoPreview(url);
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (videoFile) {
      const formData = new FormData();
      formData.append('video_file', videoFile);
      formData.append('title', videoFile.name);
      mutation.mutate(formData);
    }
  };

  return (
    <LabPage>
      <LabHeader
        code="Protocole · DCS"
        title="Cinematic"
        accent="Reconstruction"
        lede={t(
          'labs.cinematic.subtitle',
          'Transformez vos séquences 2D en environnements 3D volumétriques temporels.',
        )}
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Configuration & Upload */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel
            title={t('labs.cinematic.video_source', 'Source Vidéo')}
            corner="Dynamic Cinematic Splatting"
          >
            <form onSubmit={onSubmit} className="space-y-6">
              <div className="group relative">
                <input
                  type="file"
                  accept="video/*"
                  onChange={onFileChange}
                  aria-label={t('labs.cinematic.video_source_aria', 'Importer une vidéo source')}
                  className="absolute inset-0 z-10 h-full w-full cursor-pointer opacity-0"
                />
                <div
                  className={`flex aspect-video w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed p-6 transition-colors ${
                    videoFile
                      ? 'border-[#FDB913]/50 bg-[#FDB913]/5'
                      : 'border-[#F4F1E8]/15 bg-[#0B0C10] group-hover:border-[#F4F1E8]/30'
                  }`}
                >
                  {videoPreview ? (
                    <video
                      src={videoPreview}
                      className="h-full w-full rounded-xl object-cover"
                      muted
                      aria-label={t(
                        'labs.cinematic.video_preview_aria',
                        'Aperçu de la vidéo source',
                      )}
                    />
                  ) : (
                    <>
                      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016]">
                        <Video className="h-6 w-6 text-[#8F94A5]" aria-hidden="true" />
                      </div>
                      <p className="text-center text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                        Glisse une vidéo ou clique pour parcourir
                      </p>
                    </>
                  )}
                </div>
              </div>

              {videoFile && (
                <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
                  <p className={`${LAB_LABEL} mb-1`}>
                    {t('labs.cinematic.selected_file', 'Fichier sélectionné')}
                  </p>
                  <p className="truncate text-sm font-bold text-[#F4F1E8]">{videoFile.name}</p>
                  <p className="text-[10px] font-bold text-[#8F94A5]">
                    {(videoFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              )}

              <button type="submit" disabled={mutation.isPending || !videoFile} className={LAB_CTA}>
                {mutation.isPending ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  t('labs.cinematic.reconstruction_title', 'LANCER LA RECONSTRUCTION')
                )}
              </button>
            </form>
          </LabPanel>

          <LabPanel title="Pipeline DCS">
            <ul className="space-y-4">
              <li className="flex gap-3 text-xs leading-relaxed text-[#8F94A5]">
                <Target className="h-4 w-4 shrink-0 text-[#FDB913]" aria-hidden="true" />{' '}
                {t('labs.cinematic.temporal_sampling', 'Échantillonnage temporel à 2 FPS.')}
              </li>
              <li className="flex gap-3 text-xs leading-relaxed text-[#8F94A5]">
                <Target className="h-4 w-4 shrink-0 text-[#FDB913]" aria-hidden="true" />{' '}
                {t('labs.cinematic.depth_inference', 'Inférence de profondeur via MiDaS SOTA.')}
              </li>
              <li className="flex gap-3 text-xs leading-relaxed text-[#8F94A5]">
                <Target className="h-4 w-4 shrink-0 text-[#FDB913]" aria-hidden="true" />{' '}
                Reconstruction par Gaussian Splatting.
              </li>
            </ul>
          </LabPanel>
        </div>

        {/* Visualisation 3D / Résultats */}
        <div className="lg:col-span-8">
          <AnimatePresence mode="wait">
            {mutation.isPending ? (
              <motion.div
                key="pending"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex h-full flex-col items-center justify-center py-24 text-center"
              >
                <div className="relative mb-8 h-32 w-32">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
                    className="absolute inset-0 rounded-full border-t-4 border-[#FDB913]"
                  />
                  <Box
                    className="absolute left-1/2 top-1/2 h-16 w-16 -translate-x-1/2 -translate-y-1/2 animate-pulse text-[#F4F1E8]"
                    aria-hidden="true"
                  />
                </div>
                <h3 className="font-manga mb-2 text-2xl font-black uppercase italic text-[#F4F1E8]">
                  {t('labs.cinematic.reconstruction_title', 'Reconstruction Sémantique')}
                </h3>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#8F94A5]">
                  {t(
                    'labs.cinematic.reconstruction_progress',
                    'Génération de la volumétrie temporelle...',
                  )}
                </p>
              </motion.div>
            ) : reconstructionResult ? (
              <motion.div
                key="result"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-8"
              >
                {/* Scène 3D */}
                <LabPanel
                  title="Scène 3D dynamique"
                  corner={
                    <span className="flex items-center gap-1.5">
                      <Maximize2 className="h-3.5 w-3.5" aria-hidden="true" /> Processed
                    </span>
                  }
                >
                  <div className="relative aspect-video overflow-hidden rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]">
                    {/* Virtual Viewer Placeholder */}
                    <div className="flex h-full items-center justify-center p-12 text-center">
                      <div>
                        <Zap
                          className="mx-auto mb-6 h-16 w-16 animate-pulse text-[#FDB913]"
                          aria-hidden="true"
                        />
                        <h4 className="font-manga mb-2 text-3xl font-black uppercase italic text-[#F4F1E8]">
                          {t('labs.cinematic.scene_ready', 'Scene Ready')}
                        </h4>
                        <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-[#8F94A5]">
                          {t(
                            'labs.cinematic.scene_ready_desc',
                            'Utilisez le moteur DCS pour naviguer dans la scène',
                          )}
                        </p>
                      </div>
                    </div>

                    {/* Timeline Controls Overlay */}
                    <div className="absolute bottom-0 left-0 flex w-full items-center gap-6 bg-gradient-to-t from-[#0B0C10]/90 to-transparent p-8">
                      <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] p-3">
                        <Play className="h-5 w-5 text-[#F4F1E8]" aria-hidden="true" />
                      </div>
                      <div className="h-1 flex-grow overflow-hidden rounded-full bg-[#F4F1E8]/10">
                        <div className="h-full w-1/3 bg-[#FDB913]" />
                      </div>
                      <span className="font-mono text-[10px] font-black text-[#F4F1E8]">
                        00:01.5 / 00:04.2
                      </span>
                    </div>
                  </div>
                </LabPanel>

                {/* Frames Grid */}
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {reconstructionResult.frames.map((frame: DCSFrame, i: number) => (
                    <div
                      key={i}
                      className="group rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-4 transition-colors hover:border-[#FDB913]/40"
                    >
                      <div className="relative mb-4 aspect-square overflow-hidden rounded-xl bg-[#0B0C10]">
                        <img
                          src={frame.model_url}
                          alt={`Frame ${i}`}
                          className="h-full w-full object-cover opacity-50 grayscale transition-all group-hover:opacity-100 group-hover:grayscale-0"
                          loading="lazy"
                          decoding="async"
                        />
                        <span className="absolute left-3 top-3 rounded-full border border-[#FDB913]/40 bg-[#0B0C10]/80 px-2.5 py-1 text-[9px] font-black uppercase tracking-widest text-[#FDB913]">
                          T+{frame.timestamp.toFixed(1)}s
                        </span>
                      </div>
                      <div className="flex items-center justify-between px-2">
                        <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                          Points: {frame.point_count}
                        </span>
                        <div className="flex h-6 w-6 items-center justify-center rounded-lg bg-[#FDB913]/10 text-[#FDB913]">
                          <ChevronRight className="h-4 w-4" aria-hidden="true" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            ) : (
              <LabEmpty
                icon={<Video className="h-20 w-20" aria-hidden="true" />}
                title={t('labs.cinematic.waiting_engine_title', 'Moteur en attente')}
                hint={t(
                  'labs.cinematic.waiting_engine_desc',
                  'Chargez une séquence vidéo pour démarrer le DCS.',
                )}
              />
            )}
          </AnimatePresence>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Importe une séquence',
            body: 'Glisse une vidéo 2D classique dans la zone de dépôt : le système va en reconstruire une version 3D explorable, image par image.',
          },
          {
            title: 'Lance la reconstruction',
            body: 'Clique sur « Lancer la reconstruction » et laisse le traitement se terminer. Chaque frame reconstruite apparaît dans la grille de résultats.',
          },
          {
            title: 'Juge la densité',
            body: "Chaque vignette indique son horodatage et son nombre de points 3D, ce qui permet d'évaluer la finesse de la scène reconstruite.",
          },
        ]}
        note="La vidéo est échantillonnée à 2 images par seconde, puis chaque frame passe par une estimation de profondeur monoculaire (MiDaS). Les cartes de profondeur sont ensuite converties en nuages de points par Gaussian Splatting, produisant une frame volumétrique horodatée avec son nombre de points."
      />
    </LabPage>
  );
};

export default CinematicReconstructionPage;
