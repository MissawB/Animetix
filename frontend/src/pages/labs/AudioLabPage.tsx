import React, { useState, useEffect } from 'react';
import { Mic, MicOff, Play, Save, Trash2, Wand2, Search, Star, User, ArrowRight } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useTranslation } from 'react-i18next';
import { useAudioLab } from '../../features/labs/hooks/useAudioLab';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { CardSkeleton } from "../../components/ui/Skeleton";

const audioSchema = z.object({
  text: z.string().min(10, "Veuillez entrer au moins 10 caractères pour la synthèse.").max(500, "Le texte est trop long."),
});

type AudioFormValues = z.infer<typeof audioSchema>;

interface Recording {
  id: number;
  name: string;
  duration: string;
}

const AudioLabPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data, loading, processAudio, searchSeiyuu, seiyuuResults, isSearchingSeiyuu } = useAudioLab();
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [seiyuuQuery, setSeiyuuQuery] = useState('');
  const [isDraggingOver, setIsDraggingOver] = useState(false);
  const [selectedSeiyuu, setSelectedSeiyuu] = useState<Seiyuu | null>(null);

  const { register, handleSubmit, formState: { errors } } = useForm<AudioFormValues>({
    resolver: zodResolver(audioSchema),
    defaultValues: { text: '' }
  });

  // Fetch initial seiyuu list
  useEffect(() => {
    searchSeiyuu('');
  }, [searchSeiyuu]);

  const startRecording = () => setIsRecording(true);
  const stopRecording = () => {
    setIsRecording(false);
    setSelectedSeiyuu(null);
    setRecordings([...recordings, { id: Date.now(), name: `Extrait #${recordings.length + 1}`, duration: '0:12' }]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioFile(file);
      setSelectedSeiyuu(null);
      setRecordings([{ id: Date.now(), name: file.name, duration: 'N/A' }]);
    }
  };

  const onDragStart = (e: React.DragEvent, seiyuu: Seiyuu) => {
    e.dataTransfer.setData('seiyuu', JSON.stringify(seiyuu));
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(true);
  };

  const onDragLeave = () => {
    setIsDraggingOver(false);
  };

  const onDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDraggingOver(false);
    const seiyuuData = e.dataTransfer.getData('seiyuu');
    if (seiyuuData) {
      const seiyuu = JSON.parse(seiyuuData);
      setSelectedSeiyuu(seiyuu);
      setRecordings([{ id: Date.now(), name: `Voix de ${seiyuu.name}`, duration: 'Sample' }]);
      
      // Fetch the sample and convert to File to satisfy the existing backend
      try {
          const resp = await fetch(seiyuu.sample_url);
          if (resp.ok) {
              const blob = await resp.blob();
              const file = new File([blob], `${seiyuu.name}_sample.wav`, { type: 'audio/wav' });
              setAudioFile(file);
          }
      } catch (err) {
          console.error("Failed to load seiyuu sample:", err);
      }
    }
  };

  const onSubmit = async (values: AudioFormValues) => {
    await processAudio({
        text: values.text,
        audio_file: audioFile,
        source_type: audioFile ? 'upload' : 'library'
    });
  };

  const playResult = () => {
    if (data?.audio_url) {
        const audio = new Audio(data.audio_url);
        audio.play();
    }
  };

  if (loading) return (
    <div className="max-w-6xl mx-auto px-6 py-16">
        <CardSkeleton />
    </div>
  );

  return (
    <div className="max-w-[1600px] mx-auto px-6 py-16">
      <header className="mb-12">
        <h1 className="text-6xl font-black italic manga-font mb-4 tracking-tighter uppercase">
          {t('labs.audio.title')}
        </h1>
        <p className="text-gray-500 font-bold uppercase tracking-widest">{t('labs.audio.cloning')}</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Main Recording & Cloning Area (Left & Center) */}
        <div className="lg:col-span-8 space-y-12">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Recording Panel */}
                <div className="md:col-span-1">
                    <Card 
                        padding="lg" 
                        className={`h-fit transition-all duration-300 ${isDraggingOver ? 'ring-4 ring-blue-500 bg-blue-500/10 scale-105' : ''}`}
                        onDragOver={onDragOver}
                        onDragLeave={onDragLeave}
                        onDrop={onDrop}
                    >
                        <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                            <Mic className="w-4 h-4" /> Source Vocale
                        </h3>
                        
                        <div className="flex flex-col items-center py-6">
                            <button 
                                onClick={isRecording ? stopRecording : startRecording}
                                className={`w-24 h-24 rounded-full flex items-center justify-center transition-all shadow-2xl ${isRecording ? 'bg-red-500 animate-pulse scale-110' : selectedSeiyuu ? 'bg-blue-600 text-white' : 'bg-black text-white hover:scale-105'}`}
                                aria-label={isRecording ? 'Arrêter l\'enregistrement' : 'Démarrer l\'enregistrement'}
                            >
                                {isRecording ? <MicOff className="w-8 h-8" /> : selectedSeiyuu ? <Star className="w-8 h-8 fill-current" /> : <Mic className="w-8 h-8" />}
                            </button>
                            <span className={`mt-6 font-black italic uppercase tracking-widest text-[9px] ${isRecording ? 'text-red-500' : selectedSeiyuu ? 'text-blue-500' : 'opacity-40'}`}>
                                {isRecording ? 'Enregistrement...' : selectedSeiyuu ? `Voix: ${selectedSeiyuu.name}` : 'Prêt à enregistrer'}
                            </span>
                            {selectedSeiyuu && (
                                <p className="text-[7px] font-bold uppercase opacity-30 mt-1">Glissez un autre seiyuu pour changer</p>
                            )}
                        </div>

                        <div className="relative mb-6">
                            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-black/5 dark:border-white/5"></div></div>
                            <div className="relative flex justify-center text-[9px] uppercase font-black"><span className="px-2 bg-white dark:bg-navy-800 text-gray-400">ou</span></div>
                        </div>

                        <Button 
                            variant="outline"
                            fullWidth
                            onClick={() => document.getElementById('audio-upload')?.click()}
                            className="text-[10px] py-3"
                        >
                            Importer .wav
                        </Button>
                        <input type="file" id="audio-upload" className="hidden" accept=".wav,.mp3" onChange={handleFileChange} />

                        <div className="mt-8 space-y-3">
                            {recordings.map((rec) => (
                                <div key={rec.id} className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl flex items-center justify-between group">
                                    <div className="flex items-center gap-2">
                                        <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-white ${selectedSeiyuu ? 'bg-blue-600' : 'bg-blue-500'}`}>
                                            <Play className="w-3 h-3 fill-current" />
                                        </div>
                                        <span className="font-bold text-[9px] truncate max-w-[80px]">{rec.name}</span>
                                    </div>
                                    <button 
                                      type="button"
                                      aria-label="Supprimer l'enregistrement"
                                      className="p-1 hover:bg-red-500/10 rounded transition-all opacity-0 group-hover:opacity-100 border-none bg-transparent cursor-pointer"
                                      onClick={() => { setRecordings([]); setAudioFile(null); setSelectedSeiyuu(null); }}
                                    >
                                      <Trash2 className="w-3 h-3 text-red-500" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    </Card>
                </div>

                {/* Cloning Panel */}
                <div className="md:col-span-2 space-y-8">
                    <Card padding="lg" className="relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-8 opacity-5">
                            <Wand2 className="w-40 h-42 text-purple-500" />
                        </div>
                        
                        <h3 className="text-3xl font-black italic manga-font mb-8">FORGE <span className="text-purple-500">VOCALE</span></h3>
                        
                        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-8">
                            <div className="flex flex-col gap-2">
                                <textarea 
                                    {...register('text')}
                                    className={`w-full p-8 rounded-[2rem] bg-gray-50 dark:bg-gray-800 outline-none font-medium text-lg min-h-[200px] transition-all 
                                        ${errors.text ? 'ring-2 ring-red-500' : 'focus:ring-2 focus:ring-purple-500'}
                                    `}
                                    placeholder={selectedSeiyuu ? `Faites parler ${selectedSeiyuu.name}...` : "Tapez le texte que l'IA doit dire avec votre voix..."}
                                ></textarea>
                                {errors.text && <span className="text-red-500 text-xs font-black pl-4">{errors.text.message}</span>}
                            </div>

                            <Button 
                                type="submit"
                                variant="primary"
                                size="lg"
                                fullWidth
                                disabled={(recordings.length === 0 && !audioFile)}
                                className="bg-gradient-to-r from-purple-600 to-blue-600 border-none py-6"
                            >
                                <Save className="w-6 h-6 mr-2" /> {selectedSeiyuu ? `Synthétiser ${selectedSeiyuu.name}` : t('labs.audio.generate')}
                            </Button>
                        </form>
                    </Card>

                    {data?.audio_url && (
                        <div className="bg-green-500/10 border-2 border-green-500 p-8 rounded-[2.5rem] flex items-center justify-between animate-slide-up">
                            <div>
                                <h4 className="font-black text-green-500 italic text-xl uppercase leading-none mb-1">RÉSULTAT PRÊT !</h4>
                                <p className="font-bold opacity-60 text-sm">Votre voix a été synthétisée avec succès.</p>
                            </div>
                            <Button 
                                variant="success"
                                className="p-4 rounded-2xl"
                                onClick={playResult}
                            >
                                <Play className="w-6 h-6 fill-current" />
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>

        <aside className="lg:col-span-4 space-y-8">
            <div className="space-y-4">
                <div className="flex justify-between items-end gap-4">
                    <div className="space-y-1">
                        <h2 className="text-2xl font-black italic manga-font uppercase">Seiyuu <span className="text-blue-500">Discovery</span></h2>
                        <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">Catalogue des voix légendaires.</p>
                    </div>
                    <Button 
                        variant="ghost" 
                        className="p-0 text-[9px] font-black uppercase tracking-widest text-blue-500 hover:text-blue-400 transition-colors group mb-1"
                        onClick={() => navigate('/lab/audio/seiyuu/')}
                    >
                        Plein Écran <ArrowRight className="w-3 h-3 inline group-hover:translate-x-1 transition-transform" />
                    </Button>
                </div>
                <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input 
                        type="text" 
                        placeholder="Seiyuu ou personnage..."
                        value={seiyuuQuery}
                        onChange={(e) => {
                            setSeiyuuQuery(e.target.value);
                            searchSeiyuu(e.target.value);
                        }}
                        className="w-full pl-12 pr-4 py-4 rounded-2xl bg-gray-50 dark:bg-gray-800 border-none outline-none focus:ring-2 focus:ring-blue-500 font-bold text-sm transition-all"
                    />
                    {isSearchingSeiyuu && <div className="absolute right-4 top-1/2 -translate-y-1/2 w-3 h-3 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />}
                </div>
            </div>

            <div className="space-y-6 max-h-[800px] overflow-y-auto pr-2 custom-scrollbar">
                {seiyuuResults.map((s: Seiyuu, idx: number) => (
                    <div 
                        key={idx} 
                        draggable 
                        onDragStart={(e) => onDragStart(e, s)}
                        className="cursor-grab active:cursor-grabbing"
                    >
                        <Card padding="md" className="group border-none relative overflow-hidden transition-all hover:ring-2 hover:ring-blue-500/50">
                            <div className="flex justify-between items-start mb-3">
                                <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                                    <User className="w-4 h-4" />
                                </div>
                                <Badge variant="neutral" className="text-[7px] font-black uppercase tracking-tighter opacity-40">JAPANESE VA</Badge>
                            </div>
                            
                            <h4 className="text-lg font-black uppercase tracking-tight mb-0.5">{s.name}</h4>
                            <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest mb-4 leading-relaxed line-clamp-1">{s.role || 'Seiyuu'}</p>
                            
                            <div className="space-y-3">
                                <div className="space-y-1">
                                    <span className="text-[8px] font-black uppercase text-blue-500 tracking-widest flex items-center gap-1">
                                        <Star className="w-2.5 h-2.5 fill-current" /> Rôles
                                    </span>
                                    <p className="text-[10px] font-medium leading-relaxed italic opacity-80 line-clamp-2">{s.role}</p>
                                </div>
                                
                                <div className="pt-3 border-t border-black/5 dark:border-white/5 space-y-1">
                                    <p className="text-[9px] leading-relaxed opacity-60 line-clamp-2">Talent vocal certifié.</p>
                                </div>
                            </div>
                            
                            <div className="mt-4 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <div className="flex-1 h-1 bg-blue-500/20 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 w-full animate-pulse" />
                                </div>
                                <span className="text-[7px] font-black uppercase text-blue-500">Glisser pour cloner</span>
                            </div>
                        </Card>
                    </div>
                ))}
                
                {seiyuuResults.length === 0 && !isSearchingSeiyuu && (
                    <div className="py-20 text-center opacity-20">
                        <Search className="w-8 h-8 mx-auto mb-4" />
                        <p className="text-[10px] font-black uppercase tracking-widest">Aucun résultat</p>
                    </div>
                )}
            </div>
        </aside>
      </div>
    </div>
  );
};

export default AudioLabPage;


