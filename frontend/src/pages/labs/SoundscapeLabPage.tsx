import React, { useState } from 'react';
import { Volume2, Music, Video, Wand2 } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { useTranslation } from 'react-i18next';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_CTA,
  LAB_BTN_GHOST,
} from './components/shared/LabKit';

interface SoundscapeResult {
  status: string;
  audio_url: string;
}

const SoundscapeLabPage: React.FC = () => {
  const { t } = useTranslation();
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [result, setResult] = useState<SoundscapeResult | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!videoFile) return;
      const formData = new FormData();
      formData.append('video_file', videoFile);

      return apiClient('/api/v1/labs/soundscape/', {
        method: 'POST',
        body: formData,
        headers: {},
      });
    },
    onSuccess: (data) => {
      setResult(data);
    },
  });

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      setVideoPreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Soundscape"
        title="Paysage"
        accent="sonore"
        lede={t(
          'labs.soundscape.subtitle',
          "Génération d'ambiances sonores par IA AudioLDM basées sur l'analyse visuelle.",
        )}
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Controls */}
        <div className="space-y-8 lg:col-span-4">
          <LabPanel title={t('labs.soundscape.orchestrator_title', 'Orchestrateur audio')}>
            <div className="space-y-4">
              <button
                type="button"
                onClick={() => document.getElementById('video-sound-upload')?.click()}
                className={`${LAB_BTN_GHOST} w-full justify-center rounded-xl py-3.5`}
              >
                {videoFile
                  ? t('labs.soundscape.change_video', 'Changer la vidéo')
                  : t('labs.soundscape.load_video', 'Charger une vidéo')}
              </button>
              <input
                type="file"
                id="video-sound-upload"
                aria-label={t('labs.soundscape.load_video', 'Charger une vidéo')}
                className="hidden"
                accept="video/*"
                onChange={handleUpload}
              />

              <button
                type="button"
                onClick={() => mutation.mutate()}
                disabled={!videoFile || mutation.isPending}
                className={LAB_CTA}
              >
                <Wand2 className="h-5 w-5" aria-hidden="true" />{' '}
                {t('labs.soundscape.generate_btn', "Générer l'ambiance")}
              </button>
            </div>
          </LabPanel>

          <LabPanel title={t('labs.soundscape.how_title', 'Comment ça marche')}>
            <p className="text-sm leading-relaxed text-[#8F94A5]">
              {t(
                'labs.soundscape.desc',
                "L'IA analyse d'abord les objets et les actions présentes dans votre vidéo (via Video-LLaVA) pour construire un prompt sonore sémantiquement cohérent.",
              )}
            </p>
          </LabPanel>
        </div>

        {/* Viewport */}
        <div className="lg:col-span-8">
          <div className="relative flex min-h-[600px] items-center justify-center overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8">
            {mutation.isPending && (
              <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-[#0B0C10]/90 px-12 text-center backdrop-blur-md">
                <div className="mb-8 h-24 w-24 animate-spin rounded-full border-4 border-[#FDB913] border-t-transparent"></div>
                <h2 className="font-manga mb-4 text-3xl font-black uppercase italic text-[#F4F1E8]">
                  {t('labs.soundscape.composing', 'Composition AudioLDM…')}
                </h2>
                <p className="font-black uppercase tracking-[0.2em] text-[#FDB913]">
                  {t('labs.soundscape.synthesizing', 'Synthèse du spectre sonore latent…')}
                </p>
              </div>
            )}

            {!videoPreview ? (
              <LabEmpty
                icon={<Video className="h-20 w-20" aria-hidden="true" />}
                title={t('labs.soundscape.no_video', 'Aucune source vidéo')}
                hint={t(
                  'labs.soundscape.no_video_hint',
                  "Charge un clip vidéo depuis le panneau de gauche : l'IA en déduira l'ambiance sonore.",
                )}
              />
            ) : (
              <div className="flex h-full w-full flex-col gap-12 animate-fade-in">
                <div className="space-y-4">
                  <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                    {t('labs.soundscape.source_video', 'Vidéo source')}
                  </span>
                  <div className="aspect-video overflow-hidden rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]">
                    <video
                      src={videoPreview}
                      controls
                      aria-label={t('labs.soundscape.source_video', 'Vidéo source')}
                      className="h-full w-full object-cover"
                    >
                      <track kind="captions" />
                    </video>
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                      {t('labs.soundscape.generated_ambient', 'Ambiance générée')}
                    </span>
                    {result && (
                      <span className="text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                        {t('labs.soundscape.ost_synced', 'OST synchronisée')}
                      </span>
                    )}
                  </div>
                  {result ? (
                    <div className="flex items-center gap-6 rounded-xl border border-[#FDB913]/25 bg-[#0B0C10] p-8">
                      <div className="rounded-xl bg-[#FDB913] p-4 text-[#0B0C10]">
                        <Volume2 className="h-8 w-8" aria-hidden="true" />
                      </div>
                      <div className="flex-grow">
                        <audio
                          src={result.audio_url}
                          controls
                          aria-label="Ambiance sonore générée"
                          className="custom-audio-player h-12 w-full"
                        >
                          <track kind="captions" />
                        </audio>
                      </div>
                    </div>
                  ) : (
                    <div className="flex h-32 w-full items-center justify-center rounded-xl border border-dashed border-[#F4F1E8]/15 bg-[#0B0C10]">
                      <Music className="h-12 w-12 text-[#8F94A5]/40" aria-hidden="true" />
                      <span className="ml-4 text-[10px] font-black uppercase tracking-[0.3em] text-[#8F94A5]">
                        {t('labs.soundscape.ready_generation', 'Prêt pour la génération')}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: t('labs.soundscape.guide_video_title', 'La vidéo'),
            body: t(
              'labs.soundscape.guide_video_desc',
              "Chargez un clip vidéo muet ou mal sonorisé. C'est la seule chose à fournir : pas de prompt à écrire.",
            ),
          },
          {
            title: t('labs.soundscape.guide_analysis_title', "L'analyse"),
            body: t(
              'labs.soundscape.guide_analysis_desc',
              "L'IA regarde les images et identifie les objets, les lieux et les actions pour comprendre quelle ambiance sonore leur correspond.",
            ),
          },
          {
            title: t('labs.soundscape.guide_ambient_title', "L'ambiance"),
            body: t(
              'labs.soundscape.guide_ambient_desc',
              "Une piste audio d'ambiance est générée et livrée en face de votre vidéo : écoutez-la directement dans le lecteur.",
            ),
          },
        ]}
        note={`${t(
          'labs.soundscape.guide_footer_1',
          'Pipeline en deux étapes : Video-LLaVA décrit le contenu visuel de la vidéo, et cette description sert de prompt à AudioLDM pour la génération audio par diffusion latente.',
        )} ${t(
          'labs.soundscape.guide_footer_2',
          "Le résultat est une piste d'ambiance texte-vers-audio renvoyée sous forme d'URL par l'endpoint soundscape.",
        )}`}
      />
    </LabPage>
  );
};

export default SoundscapeLabPage;
