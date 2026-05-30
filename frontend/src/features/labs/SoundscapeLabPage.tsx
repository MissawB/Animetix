import React, { useState } from 'react';
import { Volume2, Music, Sparkles, Video, Play, Wand2, ArrowRight } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

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
                    <input type="file" id="video-sound-upload" className="hidden" accept="video/*" onChange={handleUpload} />

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
                                    <video src={videoPreview} controls className="w-full h-full object-cover" />
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
                                            <audio src={result.audio_url} controls className="w-full h-12 custom-audio-player" />
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
      </div>
    </AnimatedPage>
  );
};

export default SoundscapeLabPage;
