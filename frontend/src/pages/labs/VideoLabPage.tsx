import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Video, Wand2, Play, Lock, Loader2, Search } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { useAuthStore } from '../../store/authStore';
import { VideoSegment } from '../../types';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabEmpty,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_CTA,
  LAB_BTN_GHOST,
} from './components/shared/LabKit';

interface VideoLabResult {
  status: string;
  video_url: string;
  error?: string;
}

interface VideoSearchResponse {
  results: VideoSegment[];
}

const VideoLabPage: React.FC = () => {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [studioStyle, setStudioStyle] = useState<string>('Ghibli');
  const [result, setResult] = useState<VideoLabResult | null>(null);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!videoFile) return;
      const formData = new FormData();
      formData.append('video_file', videoFile);
      formData.append('studio_style', studioStyle);

      return apiClient('/api/v1/labs/video/', {
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

  const STYLES = [
    { id: 'Ghibli', name: 'Studio Ghibli' },
    { id: 'MakotoShinkai', name: 'Makoto Shinkai' },
    { id: 'Ufotable', name: 'Ufotable (Kimetsu)' },
    { id: 'MAPPA', name: 'MAPPA (Jujutsu)' },
    { id: 'Cyberpunk', name: 'Trigger (Edgerunners)' },
  ];

  const [searchQuery, setSearchQuery] = useState('');
  const [searchAuthError, setSearchAuthError] = useState(false);
  const searchMutation = useMutation<VideoSearchResponse, Error, string>({
    mutationFn: async (q: string) => {
      return apiClient(`/api/v1/labs/video/search/?q=${encodeURIComponent(q)}`, {
        method: 'GET',
      });
    },
  });

  // Video-RAG search est un mode IA (GPU) qui coûte des Berrix et requiert une session.
  // On gate avant l'appel plutôt que de laisser l'API renvoyer un 401/402 brut.
  const handleRagSearch = () => {
    if (!useAuthStore.getState().isAuthenticated) {
      setSearchAuthError(true);
      return;
    }
    setSearchAuthError(false);
    searchMutation.mutate(searchQuery);
  };

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Vidéo"
        title="Transfert"
        accent="de style"
        lede="Charge une séquence vidéo et le laboratoire la redessine dans l'esthétique d'un grand studio, image par image, en préservant le mouvement d'origine."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Controls */}
        <div className="lg:col-span-4">
          <LabPanel title="Source & style">
            <div className="space-y-6">
              <div className="space-y-2">
                <span className={LAB_LABEL}>Séquence source</span>
                <button
                  type="button"
                  onClick={() => document.getElementById('video-upload')?.click()}
                  className={`${LAB_BTN_GHOST} w-full justify-center`}
                >
                  {videoFile ? 'Changer la vidéo' : 'Charger une vidéo'}
                </button>
                <input
                  type="file"
                  id="video-upload"
                  aria-label="Charger une vidéo"
                  className="hidden"
                  accept="video/*"
                  onChange={handleUpload}
                />
              </div>

              <div className="space-y-2">
                <span className={LAB_LABEL}>Studio artistique</span>
                <div className="grid grid-cols-1 gap-2">
                  {STYLES.map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setStudioStyle(s.id)}
                      className={`cursor-pointer rounded-xl border px-4 py-3 text-left text-xs font-bold transition-colors ${
                        studioStyle === s.id
                          ? 'border-[#FDB913] bg-[#FDB913]/10 text-[#F4F1E8]'
                          : 'border-[#F4F1E8]/10 bg-transparent text-[#8F94A5] hover:border-[#F4F1E8]/30 hover:text-[#F4F1E8]'
                      }`}
                    >
                      {s.name}
                    </button>
                  ))}
                </div>
              </div>

              <button
                type="button"
                onClick={() => mutation.mutate()}
                disabled={!videoFile || mutation.isPending}
                className={LAB_CTA}
              >
                {mutation.isPending ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <>
                    <Wand2 className="h-5 w-5" aria-hidden="true" /> Générer l'anime
                  </>
                )}
              </button>
            </div>
          </LabPanel>
        </div>

        {/* Viewport */}
        <div className="space-y-8 lg:col-span-8">
          <LabPanel title="Visionneuse" corner={result ? 'Rendu prêt' : studioStyle}>
            <div className="relative min-h-[480px]">
              {mutation.isPending && (
                <div className="absolute inset-0 z-10 flex flex-col items-center justify-center rounded-xl bg-[#0B0C10]/90 px-8 text-center">
                  <Loader2
                    className="mb-6 h-12 w-12 animate-spin text-[#E8442B]"
                    aria-hidden="true"
                  />
                  <h2 className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]">
                    Traitement FateZero en cours
                  </h2>
                  <p className="mt-3 text-xs font-black uppercase tracking-widest text-[#FDB913]">
                    Reconstruction temporelle des vecteurs de mouvement…
                  </p>
                  <p className="mt-8 text-[10px] font-bold uppercase text-[#8F94A5]">
                    Cette opération est très coûteuse en VRAM. Merci de patienter.
                  </p>
                </div>
              )}

              {!videoPreview ? (
                <LabEmpty
                  icon={<Video className="h-20 w-20" aria-hidden="true" />}
                  title="Aucune source vidéo"
                  hint="Charge une séquence depuis le panneau Source & style : l'original et le rendu anime s'afficheront ici côte à côte."
                />
              ) : (
                <div className="grid h-full grid-cols-1 gap-6 md:grid-cols-2">
                  <div className="flex flex-col space-y-3">
                    <span className="w-fit text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                      Source originale
                    </span>
                    <div className="flex-grow overflow-hidden rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10]">
                      <video
                        src={videoPreview}
                        controls
                        aria-label="Vidéo source originale"
                        className="h-full w-full object-cover"
                      >
                        <track kind="captions" />
                      </video>
                    </div>
                  </div>
                  <div className="flex flex-col space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-black uppercase tracking-widest text-[#E8442B]">
                        Résultat anime ({studioStyle})
                      </span>
                      {result && (
                        <span className="text-[10px] font-black uppercase text-[#FDB913]">
                          Généré avec succès
                        </span>
                      )}
                    </div>
                    <div className="relative flex flex-grow items-center justify-center overflow-hidden rounded-xl border border-[#E8442B]/25 bg-[#0B0C10]">
                      {result ? (
                        <video
                          src={result.video_url}
                          controls
                          autoPlay
                          loop
                          aria-label="Vidéo anime générée"
                          className="h-full w-full object-cover"
                        >
                          <track kind="captions" />
                        </video>
                      ) : (
                        <div className="p-12 text-center">
                          <Play
                            className="mx-auto mb-4 h-16 w-16 text-[#8F94A5]/40"
                            aria-hidden="true"
                          />
                          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#8F94A5]">
                            En attente de génération
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </LabPanel>

          {/* Video-RAG Section */}
          <LabPanel title="Recherche Video-RAG" corner="Index sémantique">
            <div className="flex gap-2">
              <input
                type="text"
                aria-label="Chercher un moment dans la vidéo"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Chercher un moment…"
                className={LAB_INPUT}
              />
              <button
                type="button"
                onClick={handleRagSearch}
                disabled={!searchQuery || searchMutation.isPending}
                className={`${LAB_BTN_GHOST} flex-none disabled:cursor-not-allowed disabled:opacity-50`}
                aria-label="Lancer la recherche Video-RAG"
              >
                <Search className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
            {searchAuthError && (
              <div className="mt-6 rounded-xl border border-[#E8442B]/25 bg-[#E8442B]/[0.05] p-6 text-center">
                <Lock className="mx-auto mb-4 h-8 w-8 text-[#E8442B]" aria-hidden="true" />
                <h4 className="font-manga text-sm font-black uppercase italic text-[#F4F1E8]">
                  Connexion requise
                </h4>
                <p className="mx-auto mt-2 max-w-md text-xs leading-relaxed text-[#8F94A5]">
                  Ce mode utilise l'IA (GPU) et coûte des Berrix. Connecte-toi pour rechercher une
                  scène.
                </p>
                <Link to="/auth/login/" className={`${LAB_BTN_GHOST} mt-4 no-underline`}>
                  Se connecter
                </Link>
              </div>
            )}
            {searchMutation.isSuccess && searchMutation.data.results && (
              <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2">
                {searchMutation.data.results.map((res: VideoSegment, i: number) => (
                  <div
                    key={i}
                    className="cursor-pointer rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 transition-colors hover:border-[#FDB913]"
                  >
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-[10px] font-black text-[#FDB913]">
                        [{res.start}s - {res.end}s]
                      </span>
                      <span className="text-[9px] font-black uppercase tracking-widest text-[#8F94A5]">
                        {res.video_id}
                      </span>
                    </div>
                    <p className="line-clamp-2 text-xs leading-relaxed text-[#8F94A5]">
                      {res.summary}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </LabPanel>
        </div>
      </div>

      <LabGuide
        steps={[
          {
            title: 'Charge une séquence',
            body: 'Importe une courte vidéo personnelle : elle sert de base au transfert de style, sans retouche préalable.',
          },
          {
            title: 'Choisis un studio',
            body: "Sélectionne l'esthétique d'un grand studio (Ghibli, MAPPA, Ufotable…) qui guidera le rendu de chaque image.",
          },
          {
            title: 'Compare le rendu',
            body: "Lance la génération : la version anime s'affiche à côté de l'originale pour comparer le trait et le mouvement.",
          },
          {
            title: 'Retrouve une scène',
            body: "Le champ Video-RAG localise un moment précis dans les vidéos déjà indexées, à partir d'une simple description.",
          },
        ]}
        note="La vidéo est envoyée au backend qui applique un transfert de style image par image (algorithme FateZero) en préservant la cohérence temporelle du mouvement. La recherche Video-RAG vectorise ta requête et la compare aux résumés des segments indexés pour renvoyer les timecodes correspondants."
      />
    </LabPage>
  );
};

export default VideoLabPage;
