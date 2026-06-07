import React, { useState } from 'react';
import { 
  Box, 
  Video, 
  Upload, 
  Sparkles, 
  Zap, 
  Play, 
  Clock, 
  Layers, 
  ArrowRight,
  Loader2,
  AlertCircle,
  ChevronRight,
  Target,
  Maximize2
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../../utils/apiClient';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { AnimatedPage } from '../../../components/ui/AnimatedPage';
import { motion, AnimatePresence } from 'framer-motion';

const CinematicReconstructionPage: React.FC = () => {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [videoPreview, setVideoPreview] = useState<string | null>(null);
  const [reconstructionResult, setReconstructionResult] = useState<any>(null);

  const mutation = useMutation({
    mutationFn: (formData: FormData) => 
        apiClient('/api/v1/spatial-lab/cinematic-reconstruction/', {
            method: 'POST',
            body: formData,
            isFormData: true
        }),
    onSuccess: (data) => {
        setReconstructionResult(data);
    }
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
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Header DCS */}
        <header className="mb-16 relative">
            <div className="absolute -top-24 -left-24 w-96 h-96 bg-purple-500/10 blur-[120px] rounded-full -z-10" />
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[10px] font-black uppercase tracking-widest text-purple-400 mb-4">
                <Box className="w-3 h-3" /> DCS - Dynamic Cinematic Splatting
            </div>
            <h1 className="text-7xl font-black italic manga-font tracking-tighter uppercase mb-4">
                CINEMATIC <span className="text-purple-500 text-glow">RECONSTRUCTION</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Transformez vos séquences 2D en environnements 3D volumétriques temporels.
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
            
            {/* Configuration & Upload */}
            <div className="lg:col-span-4 space-y-8">
                <Card padding="lg" className="bg-navy-950/50 border-white/10 rounded-[3rem] shadow-2xl overflow-hidden relative">
                    <div className="absolute top-0 right-0 p-6 opacity-10">
                        <Video className="w-24 h-24 rotate-12" />
                    </div>
                    
                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Upload className="w-4 h-4 text-purple-500" /> Source Vidéo
                    </h3>

                    <form onSubmit={onSubmit} className="space-y-8">
                        <div className="relative group">
                            <input 
                                type="file" 
                                accept="video/*"
                                onChange={onFileChange}
                                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                            />
                            <div className={`w-full aspect-video rounded-[2rem] border-2 border-dashed transition-all flex flex-col items-center justify-center p-6 ${
                                videoFile ? 'border-purple-500/50 bg-purple-500/5' : 'border-white/10 bg-white/5 group-hover:border-white/20'
                            }`}>
                                {videoPreview ? (
                                    <video src={videoPreview} className="w-full h-full object-cover rounded-xl" muted />
                                ) : (
                                    <>
                                        <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center mb-4">
                                            <Video className="w-6 h-6 text-gray-400" />
                                        </div>
                                        <p className="text-[10px] font-black uppercase tracking-widest text-gray-500">Glissez ou cliquez</p>
                                    </>
                                )}
                            </div>
                        </div>

                        {videoFile && (
                            <div className="p-4 bg-white/5 rounded-2xl border border-white/5">
                                <p className="text-[10px] font-black uppercase tracking-widest text-gray-500 mb-1">Fichier sélectionné</p>
                                <p className="text-sm font-bold truncate">{videoFile.name}</p>
                                <p className="text-[10px] font-bold opacity-40">{(videoFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                            </div>
                        )}

                        <Button 
                            type="submit" 
                            disabled={mutation.isPending || !videoFile}
                            className="w-full bg-purple-600 hover:bg-purple-500 text-white py-6 rounded-2xl font-black italic text-lg uppercase shadow-xl hover:scale-105 active:scale-95 transition-all border-none"
                        >
                            {mutation.isPending ? <Loader2 className="w-6 h-6 animate-spin" /> : "LANCER LA RECONSTRUCTION"}
                        </Button>
                    </form>
                </Card>

                <Card padding="lg" className="bg-white/5 border-white/5 opacity-50">
                    <h4 className="text-[10px] font-black uppercase tracking-widest mb-4">Pipeline DCS</h4>
                    <ul className="space-y-4">
                        <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                            <Target className="w-4 h-4 text-purple-500 shrink-0" /> Échantillonnage temporel à 2 FPS.
                        </li>
                        <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                            <Target className="w-4 h-4 text-purple-500 shrink-0" /> Inférence de profondeur via MiDaS SOTA.
                        </li>
                        <li className="flex gap-3 text-[10px] font-bold uppercase leading-relaxed">
                            <Target className="w-4 h-4 text-purple-500 shrink-0" /> Reconstruction par Gaussian Splatting.
                        </li>
                    </ul>
                </Card>
            </div>

            {/* Visualisation 3D / Résultats */}
            <div className="lg:col-span-8">
                <AnimatePresence mode="wait">
                    {mutation.isPending ? (
                        <motion.div 
                            initial={{ opacity: 0 }} 
                            animate={{ opacity: 1 }} 
                            exit={{ opacity: 0 }}
                            className="h-full flex flex-col items-center justify-center py-24 text-center"
                        >
                            <div className="relative w-32 h-32 mb-8">
                                <motion.div 
                                    animate={{ rotate: 360 }}
                                    transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
                                    className="absolute inset-0 border-t-4 border-purple-500 rounded-full"
                                />
                                <Box className="w-16 h-16 text-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 animate-pulse" />
                            </div>
                            <h3 className="text-2xl font-black italic manga-font uppercase mb-2">Reconstruction Sémantique</h3>
                            <p className="text-xs font-bold opacity-30 uppercase tracking-[0.2em]">Génération de la volumétrie temporelle...</p>
                        </motion.div>
                    ) : reconstructionResult ? (
                        <motion.div 
                            initial={{ opacity: 0, y: 20 }} 
                            animate={{ opacity: 1, y: 0 }} 
                            className="space-y-8"
                        >
                            {/* 3D Timeline Preview */}
                            <Card padding="none" className="bg-black border-purple-500/30 shadow-[0_0_50px_rgba(168,85,247,0.15)] rounded-[3.5rem] overflow-hidden">
                                <div className="bg-purple-600 px-12 py-6 flex items-center justify-between">
                                    <h3 className="text-2xl font-black italic manga-font uppercase text-white flex items-center gap-4">
                                        <Maximize2 className="w-8 h-8" /> DYNAMIC 3D SCENE
                                    </h3>
                                    <Badge variant="neutral" className="bg-black/20 text-white border-none uppercase font-black italic">PROCESSED</Badge>
                                </div>
                                <div className="aspect-video bg-navy-900 relative flex items-center justify-center">
                                    <div className="absolute inset-0 opacity-20 pointer-events-none">
                                        <div className="w-full h-full bg-[radial-gradient(circle_at_center,var(--tw-gradient-from)_0%,transparent_70%)] from-purple-500/20" />
                                    </div>
                                    
                                    {/* Virtual Viewer Placeholder */}
                                    <div className="text-center p-12">
                                        <Zap className="w-20 h-20 text-purple-500 mx-auto mb-6 animate-pulse" />
                                        <h4 className="text-3xl font-black italic manga-font uppercase mb-2">Scene Ready</h4>
                                        <p className="text-[10px] font-bold opacity-40 uppercase tracking-[0.3em]">Utilisez le moteur DCS pour naviguer dans la scène</p>
                                    </div>

                                    {/* Timeline Controls Overlay */}
                                    <div className="absolute bottom-0 left-0 w-full p-8 flex items-center gap-6 bg-gradient-to-t from-black/80 to-transparent">
                                        <div className="p-3 bg-white/10 rounded-xl">
                                            <Play className="w-5 h-5 text-white" />
                                        </div>
                                        <div className="flex-grow h-1 bg-white/10 rounded-full overflow-hidden">
                                            <div className="h-full bg-purple-500 w-1/3 shadow-[0_0_10px_#a855f7]" />
                                        </div>
                                        <span className="text-[10px] font-black font-mono">00:01.5 / 00:04.2</span>
                                    </div>
                                </div>
                            </Card>

                            {/* Frames Grid */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                {reconstructionResult.frames.map((frame: any, i: number) => (
                                    <Card key={i} padding="sm" className="bg-navy-900/40 border-white/5 group hover:border-purple-500/30 transition-all">
                                        <div className="aspect-square bg-black rounded-2xl mb-4 overflow-hidden relative">
                                            <img src={frame.model_url} alt={`Frame ${i}`} className="w-full h-full object-cover opacity-50 grayscale group-hover:grayscale-0 group-hover:opacity-100 transition-all" />
                                            <div className="absolute top-3 left-3">
                                                <Badge variant="neutral" className="bg-black/60 text-white border-none text-[8px]">T+{frame.timestamp.toFixed(1)}s</Badge>
                                            </div>
                                        </div>
                                        <div className="flex justify-between items-center px-2">
                                            <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">Points: {frame.point_count}</span>
                                            <div className="w-6 h-6 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-500">
                                                <ChevronRight className="w-4 h-4" />
                                            </div>
                                        </div>
                                    </Card>
                                ))}
                            </div>
                        </motion.div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center py-32 opacity-10 text-center border-4 border-dashed border-white/5 rounded-[4rem]">
                            <Video className="w-32 h-32 mb-8" />
                            <h3 className="text-4xl font-black italic manga-font uppercase mb-4">Moteur en attente</h3>
                            <p className="text-sm font-bold uppercase tracking-[0.3em]">Chargez une séquence vidéo pour démarrer le DCS.</p>
                        </div>
                    )}
                </AnimatePresence>
            </div>
        </div>

        {/* Technical Specs Footer */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <Clock className="w-8 h-8 text-gray-500 mb-4" />
                <h4 className="text-xs font-black uppercase tracking-widest mb-2 text-white">Échantillonnage Temporel</h4>
                <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Le DCS analyse 24 frames par seconde mais n'extrait que les segments de haute variance pour optimiser la reconstruction.</p>
            </Card>
            <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <Layers className="w-8 h-8 text-purple-500 mb-4" />
                <h4 className="text-xs font-black uppercase tracking-widest mb-2 text-white">Gaussian Splatting</h4>
                <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Utilisation de splats 3D asymétriques pour représenter la transparence et les effets de lumière volumétriques dynamiques.</p>
            </Card>
            <Card padding="lg" className="bg-navy-900/40 border-white/5">
                <Zap className="w-8 h-8 text-yellow-500 mb-4" />
                <h4 className="text-xs font-black uppercase tracking-widest mb-2 text-white">Accélération GPU</h4>
                <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed">Pipeline d'inférence distribué sur clusters H100 pour garantir un temps de rendu sub-temporel.</p>
            </Card>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default CinematicReconstructionPage;

