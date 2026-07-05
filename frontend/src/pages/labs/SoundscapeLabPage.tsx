import React, { useState } from 'react';
import { Volume2, Music, Sparkles, Video, Wand2 } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";

interface SoundscapeResult {
  status: string;
  audio_url: string;
}

const SoundscapeLabPage: React.FC = () => {
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
            headers: {}
        });
    },
    onSuccess: (data) => {
        setResult(data);
    }
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
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-16">
            <h1 className="text-6xl font-black italic manga-font mb-4 tracking-tighter uppercase">
                SOUNDSCAPE <span className="text-emerald-500 text-glow">LAB</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Génération d'ambiances sonores par IA AudioLDM basées sur l'analyse visuelle.
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
            {/* Controls */}
            <div className="lg:col-span-1 space-y-8">
                <Card padding="lg" className="h-fit">
                    <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                        <Music className="w-4 h-4" /> Orchestrateur Audio
                    </h3>
                    
                    <Button 
                        onClick={() => document.getElementById('video-sound-upload')?.click()}
                        variant="outline"
                        fullWidth
                        className="mb-6 bg-black text-white hover:bg-gray-900 border-none"
                    >
                        {videoFile ? 'CHANGER LA VIDÉO' : 'CHARGER UNE VIDÉO'}
                    </Button>
                    <input type="file" id="video-sound-upload" aria-label="Charger une vidéo" className="hidden" accept="video/*" onChange={handleUpload} />

                    <Button 
                        onClick={() => mutation.mutate()}
                        disabled={!videoFile || mutation.isPending}
                        variant="primary"
                        fullWidth
                        className="bg-emerald-600 hover:bg-emerald-700 text-white border-none py-6"
                    >
                        <Wand2 className="w-5 h-5" /> GÉNÉRER L'AMBIANCE
                    </Button>
                </Card>

                <Card padding="lg" className="bg-navy-900/50 text-white/40 border-white/5">
                    <Sparkles className="w-12 h-12 mb-4 text-emerald-400 opacity-20" />
                    <p className="text-xs font-bold leading-relaxed italic">
                        L'IA analyse d'abord les objets et les actions présentes dans votre vidéo (via Video-LLaVA) pour construire un prompt sonore sémantiquement cohérent.
                    </p>
                </Card>
            </div>

            {/* Viewport */}
            <div className="lg:col-span-3">
                <div className="bg-black rounded-[4rem] shadow-2xl overflow-hidden min-h-[600px] relative border-4 border-white/5 flex items-center justify-center p-8">
                    {mutation.isPending && (
                        <div className="absolute inset-0 bg-black/80 backdrop-blur-md z-50 flex flex-col items-center justify-center text-center px-12">
                            <div className="w-24 h-24 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mb-8 shadow-[0_0_30px_rgba(16,185,129,0.5)]"></div>
                            <h2 className="text-3xl font-black italic manga-font text-white mb-4 uppercase text-glow">Composition AudioLDM...</h2>
                            <p className="text-emerald-400 font-bold uppercase tracking-[0.2em] animate-pulse">Synthèse du spectre sonore latent...</p>
                        </div>
                    )}

                    {!videoPreview ? (
                        <div className="text-center opacity-10 animate-pulse">
                            <Video className="w-40 h-40 mx-auto mb-6" />
                            <span className="text-2xl font-black italic manga-font uppercase">Aucune source vidéo</span>
                        </div>
                    ) : (
                        <div className="flex flex-col gap-12 w-full h-full animate-fade-in">
                            <div className="space-y-4">
                                <Badge variant="neutral" className="bg-white/10 text-white border-white/10">Vidéo Source</Badge>
                                <div className="aspect-video bg-gray-900 rounded-3xl overflow-hidden border border-white/5">
                                    <video src={videoPreview} controls aria-label="Vidéo source" className="w-full h-full object-cover">
                                        <track kind="captions" />
                                    </video>
                                </div>
                            </div>
                            
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <Badge variant="primary" className="bg-emerald-600">Ambiance Générée</Badge>
                                    {result && <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">OST Synchronisée</span>}
                                </div>
                                {result ? (
                                    <div className="bg-navy-900/50 p-8 rounded-3xl border-2 border-emerald-500/20 flex items-center gap-6">
                                        <div className="p-4 bg-emerald-500 rounded-2xl shadow-[0_0_20px_rgba(16,185,129,0.4)]">
                                            <Volume2 className="w-8 h-8 text-white" />
                                        </div>
                                        <div className="flex-grow">
                                            <audio src={result.audio_url} controls aria-label="Ambiance sonore générée" className="w-full h-12 custom-audio-player">
                                                <track kind="captions" />
                                            </audio>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="w-full h-32 bg-white/5 rounded-3xl flex items-center justify-center border border-white/5 border-dashed">
                                        <Music className="w-12 h-12 text-white opacity-10" />
                                        <span className="text-[10px] font-black uppercase text-white/10 tracking-[0.3em] ml-4">Prêt pour la génération</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>

        {/* Guide & Protocole */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card padding="lg" className="bg-white dark:bg-black/40 border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.1)] relative overflow-hidden group">
                <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Music className="w-64 h-64 text-emerald-500" />
                </div>
                <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                    <Sparkles className="w-5 h-5 text-emerald-600 dark:text-emerald-400" /> Guide du Soundscape
                </h4>
                <div className="space-y-4 relative z-10">
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-emerald-600 dark:text-emerald-400">La Vidéo :</span> Chargez un clip vidéo muet ou mal sonorisé. C'est la seule chose à fournir : pas de prompt à écrire.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-emerald-600 dark:text-emerald-400">L'Analyse :</span> L'IA regarde les images et identifie les objets, les lieux et les actions pour comprendre quelle ambiance sonore leur correspond.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
                        <span className="text-emerald-600 dark:text-emerald-400">L'Ambiance :</span> Une piste audio d'ambiance est générée et livrée en face de votre vidéo : écoutez-la directement dans le lecteur.
                    </p>
                </div>
            </Card>

            <div className="p-12 rounded-[4rem] bg-gradient-to-br from-emerald-600/10 to-transparent border border-black/5 dark:border-white/5 flex flex-col justify-center text-center">
                <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-emerald-800/70 dark:text-emerald-200/60">
                    Pipeline en deux étapes : Video-LLaVA décrit le contenu visuel de la vidéo, et cette description sert de prompt à AudioLDM pour la génération audio par diffusion latente. <br />
                    Le résultat est une piste d'ambiance texte-vers-audio renvoyée sous forme d'URL par l'endpoint soundscape.
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default SoundscapeLabPage;


