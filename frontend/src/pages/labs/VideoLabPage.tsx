import React, { useState } from 'react';
import { Video, Wand2, Play, Film, Sparkles } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { VideoSegment } from '../../types';


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

  const STYLES = [
    { id: 'Ghibli', name: 'Studio Ghibli', color: 'bg-emerald-500' },
    { id: 'MakotoShinkai', name: 'Makoto Shinkai', color: 'bg-blue-500' },
    { id: 'Ufotable', name: 'Ufotable (Kimetsu)', color: 'bg-purple-600' },
    { id: 'MAPPA', name: 'MAPPA (Jujutsu)', color: 'bg-red-600' },
    { id: 'Cyberpunk', name: 'Trigger (Edgerunners)', color: 'bg-yellow-400' },
  ];

  const [searchQuery, setSearchQuery] = useState('');
  const searchMutation = useMutation<VideoSearchResponse, Error, string>({
    mutationFn: async (q: string) => {
        return apiClient(`/api/v1/labs/video/search/?q=${encodeURIComponent(q)}`, {
            method: 'GET'
        });
    }
  });

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <header className="mb-12">
        <h1 className="text-6xl font-black italic manga-font mb-4 tracking-tighter uppercase text-center md:text-left">
          VIDEO <span className="text-red-500">LAB</span>
        </h1>
        <p className="text-white/60 text-lg">Exploitez la puissance de l'IA pour transformer vos séquences vidéo avec un transfert de style SOTA.</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
        {/* Controls */}
        <div className="lg:col-span-1 space-y-8">
            <Card padding="lg" className="h-fit">
                <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                    <Film className="w-4 h-4" /> Style Transfer SOTA
                </h3>
                
                <Button 
                    onClick={() => document.getElementById('video-upload')?.click()}
                    variant="outline"
                    fullWidth
                    className="mb-6 bg-black text-white hover:bg-gray-900 border-none"
                >
                    {videoFile ? 'CHANGER LA VIDÉO' : 'CHARGER UNE VIDÉO'}
                </Button>
                <input type="file" id="video-upload" className="hidden" accept="video/*" onChange={handleUpload} />

                <div className="space-y-4 mb-8">
                    <span className="text-[10px] font-black uppercase opacity-40 tracking-widest block">Studio Artistique</span>
                    <div className="grid grid-cols-1 gap-2">
                        {STYLES.map((s) => (
                            <button
                                key={s.id}
                                onClick={() => setStudioStyle(s.id)}
                                className={`px-4 py-3 rounded-xl text-left text-xs font-bold transition-all border-2 ${
                                    studioStyle === s.id 
                                    ? 'border-white bg-white text-black scale-105 shadow-lg' 
                                    : 'border-white/5 bg-white/5 text-white/40 hover:bg-white/10'
                                }`}
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`w-2 h-2 rounded-full ${s.color}`} />
                                    {s.name}
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                <Button 
                    onClick={() => mutation.mutate()}
                    disabled={!videoFile || mutation.isPending}
                    variant="primary"
                    fullWidth
                    className="bg-red-600 hover:bg-red-700 text-white border-none py-6 text-lg mb-4"
                >
                    <Wand2 className="w-5 h-5" /> GÉNÉRER ANIME
                </Button>
            </Card>
        </div>

        {/* Viewport */}
        <div className="lg:col-span-3 space-y-12">
            <div className="bg-black rounded-[2rem] shadow-2xl overflow-hidden min-h-[600px] relative border border-white/10 flex items-center justify-center p-4">
                {mutation.isPending && (
                    <div className="absolute inset-0 bg-black/80 backdrop-blur-md z-50 flex flex-col items-center justify-center text-center px-12">
                        <div className="w-24 h-24 border-4 border-red-500 border-t-transparent rounded-full animate-spin mb-8 shadow-[0_0_30px_rgba(239,68,68,0.5)]"></div>
                        <h2 className="text-3xl font-black italic manga-font text-white mb-4 uppercase">Traitement FateZero en cours</h2>
                        <p className="text-red-400 font-bold uppercase tracking-[0.2em] animate-pulse">Reconstruction temporelle des vecteurs de mouvement...</p>
                        <p className="text-white/20 text-[10px] mt-12 uppercase font-bold">Cette opération est très coûteuse en VRAM (H100 Cluster). Merci de patienter.</p>
                    </div>
                )}

                {!videoPreview ? (
                    <div className="text-center opacity-10">
                        <Video className="w-24 h-24 mx-auto mb-6" />
                        <span className="text-xl font-black italic manga-font uppercase tracking-widest">Aucune source vidéo</span>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full h-full animate-fade-in">
                        <div className="space-y-4 flex flex-col">
                            <Badge variant="neutral" className="bg-white/10 text-white border-white/10 w-fit">Source Originale</Badge>
                            <div className="flex-grow bg-gray-900 rounded-3xl overflow-hidden border border-white/5">
                                <video src={videoPreview} controls className="w-full h-full object-cover">
                                    <track kind="captions" />
                                </video>
                            </div>
                        </div>
                        <div className="space-y-4 flex flex-col">
                            <div className="flex justify-between items-center">
                                <Badge variant="primary" className="bg-red-600">Résultat Anime ({studioStyle})</Badge>
                                {result && <span className="text-[10px] font-black text-emerald-500 uppercase">Généré avec succès</span>}
                            </div>
                            <div className="flex-grow bg-gray-900 rounded-3xl overflow-hidden border-2 border-red-500/20 flex items-center justify-center relative">
                                {result ? (
                                    <video src={result.video_url} controls autoPlay loop className="w-full h-full object-cover">
                                        <track kind="captions" />
                                    </video>
                                ) : (
                                    <div className="text-center p-12">
                                        <Play className="w-16 h-16 text-white/5 mx-auto mb-4" />
                                        <p className="text-[10px] font-black uppercase text-white/10 tracking-[0.3em]">En attente de génération</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Video-RAG Section */}
            <Card padding="lg" className="bg-white/5 border-white/10">
                <h3 className="text-xs font-black uppercase opacity-40 mb-6 tracking-widest flex items-center gap-2">
                    <Video className="w-4 h-4" /> Video-RAG Search
                </h3>
                <div className="flex gap-2 mb-4">
                    <input 
                        type="text" 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Chercher un moment..."
                        className="bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-xs flex-grow focus:border-red-500 outline-none transition-colors"
                    />
                    <Button 
                        onClick={() => searchMutation.mutate(searchQuery)}
                        disabled={!searchQuery || searchMutation.isPending}
                        className="px-3"
                    >
                        <Wand2 className="w-4 h-4" />
                    </Button>
                </div>
                {searchMutation.isSuccess && searchMutation.data.results && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
                        {searchMutation.data.results.map((res: VideoSegment, i: number) => (
                            <div key={i} className="p-3 bg-white/5 rounded-xl border border-white/5 hover:border-white/20 transition-all cursor-pointer group">
                                <div className="flex justify-between items-center mb-1">
                                    <span className="text-[10px] font-black text-red-400">[{res.start}s - {res.end}s]</span>
                                    <Badge variant="neutral" className="text-[8px] opacity-50 uppercase">{res.video_id}</Badge>
                                </div>
                                <p className="text-[10px] leading-relaxed line-clamp-2 opacity-70 group-hover:opacity-100">{res.summary}</p>
                            </div>
                        ))}
                    </div>
                )}
            </Card>
        </div>
      </div>

      {/* Explanatory Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
        <Card padding="lg" className="bg-white/5 border-white/5 hover:border-white/10 transition-all">
          <Sparkles className="w-8 h-8 text-yellow-500 mb-4" />
          <h4 className="font-bold mb-2">Technologie FateZero</h4>
          <p className="text-xs text-white/60 leading-relaxed">
            Utilise l'algorithme FateZero pour un transfert de style temporel cohérent. L'IA reconstruit chaque frame en préservant la structure 3D, garantissant une fluidité parfaite.
          </p>
        </Card>
        <Card padding="lg" className="bg-white/5 border-white/5 hover:border-white/10 transition-all">
          <Film className="w-8 h-8 text-blue-500 mb-4" />
          <h4 className="font-bold mb-2">Video-RAG Search</h4>
          <p className="text-xs text-white/60 leading-relaxed">
            Recherchez instantanément des moments spécifiques dans vos vastes bibliothèques vidéo grâce à l'indexation sémantique avancée, facilitant la création de vos projets.
          </p>
        </Card>
        <Card padding="lg" className="bg-white/5 border-white/5 hover:border-white/10 transition-all">
          <Wand2 className="w-8 h-8 text-red-500 mb-4" />
          <h4 className="font-bold mb-2">Transformation Artistique</h4>
          <p className="text-xs text-white/60 leading-relaxed">
            Appliquez les signatures visuelles des plus grands studios d'animation (Ghibli, Mappa, Trigger...) avec une fidélité exceptionnelle, transformant vos vidéos en œuvres d'art.
          </p>
        </Card>
      </div>
    </div>
  );
};

export default VideoLabPage;


