import React, { useState } from 'react';
import { Mic, MicOff, Play, Save, Trash2, Wand2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { useTranslation } from 'react-i18next';
import { useAudioLab } from './hooks/useAudioLab';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { CardSkeleton } from '../../components/ui/Skeleton';

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
  const { data, loading, processAudio } = useAudioLab();
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [audioFile, setAudioFile] = useState<File | null>(null);

  const { register, handleSubmit, formState: { errors } } = useForm<AudioFormValues>({
    resolver: zodResolver(audioSchema),
    defaultValues: { text: '' }
  });

  const startRecording = () => setIsRecording(true);
  const stopRecording = () => {
    setIsRecording(false);
    setRecordings([...recordings, { id: Date.now(), name: `Extrait #${recordings.length + 1}`, duration: '0:12' }]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAudioFile(file);
      setRecordings([{ id: Date.now(), name: file.name, duration: 'N/A' }]);
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
    <div className="max-w-6xl mx-auto px-6 py-16">
      <h1 className="text-6xl font-black italic manga-font mb-4 tracking-tighter uppercase">
        {t('labs.audio.title')}
      </h1>
      <p className="text-gray-500 font-bold uppercase tracking-widest mb-12">{t('labs.audio.cloning')}</p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Recording Panel */}
        <Card padding="lg" className="lg:col-span-1">
            <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
                <Mic className="w-4 h-4" /> Source Vocale
            </h3>
            
            <div className="flex flex-col items-center py-6">
                <button 
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`w-28 h-28 rounded-full flex items-center justify-center transition-all shadow-2xl ${isRecording ? 'bg-red-500 animate-pulse scale-110' : 'bg-black text-white hover:scale-105'}`}
                    aria-label={isRecording ? 'Arrêter l\'enregistrement' : 'Démarrer l\'enregistrement'}
                >
                    {isRecording ? <MicOff className="w-10 h-10" /> : <Mic className="w-10 h-10" />}
                </button>
                <span className={`mt-6 font-black italic uppercase tracking-widest text-[10px] ${isRecording ? 'text-red-500' : 'opacity-40'}`}>
                    {isRecording ? 'Enregistrement...' : 'Prêt à enregistrer'}
                </span>
            </div>

            <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-black/5 dark:border-white/5"></div></div>
                <div className="relative flex justify-center text-[10px] uppercase font-black"><span className="px-2 bg-white dark:bg-navy-800 text-gray-400">ou</span></div>
            </div>

            <Button 
                variant="outline"
                fullWidth
                onClick={() => document.getElementById('audio-upload')?.click()}
                className="text-xs"
            >
                Importer un fichier .wav
            </Button>
            <input type="file" id="audio-upload" className="hidden" accept=".wav,.mp3" onChange={handleFileChange} />

            <div className="mt-8 space-y-4">
                {recordings.map((rec) => (
                    <div key={rec.id} className="p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl flex items-center justify-between group border border-gray-100 dark:border-white/5">
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white">
                                <Play className="w-4 h-4 fill-current" />
                            </div>
                            <span className="font-bold text-[10px] truncate max-w-[120px]">{rec.name}</span>
                        </div>
                        <Trash2 className="w-4 h-4 text-red-500 opacity-0 group-hover:opacity-100 cursor-pointer transition-opacity" onClick={() => { setRecordings([]); setAudioFile(null); }} />
                    </div>
                ))}
            </div>
        </Card>

        {/* Cloning Panel */}
        <div className="lg:col-span-2 space-y-8">
            <Card padding="lg" className="relative overflow-hidden">
                <div className="absolute top-0 right-0 p-8 opacity-5">
                    <Wand2 className="w-40 h-42 text-purple-500" />
                </div>
                
                <h3 className="text-3xl font-black italic manga-font mb-8">FORGE <span className="text-purple-500">VOCALE</span></h3>
                
                <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-8">
                    <div className="flex flex-col gap-2">
                        <textarea 
                            {...register('text')}
                            className={`w-full p-8 rounded-[2rem] bg-gray-50 dark:bg-navy-900 border-2 outline-none font-medium text-lg min-h-[200px] transition-all 
                                ${errors.text ? 'border-red-500 focus:ring-4 focus:ring-red-500/20' : 'border-transparent focus:border-purple-500 focus:ring-4 focus:ring-purple-500/20'}
                            `}
                            placeholder="Tapez le texte que l'IA doit dire avec votre voix..."
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
                        <Save className="w-6 h-6" /> {t('labs.audio.generate')}
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
  );
};

export default AudioLabPage;
