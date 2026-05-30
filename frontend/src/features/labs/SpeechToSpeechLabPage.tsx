import React, { useState, useRef } from 'react';
import { Mic, Square, Play, Volume2, Sparkles, Radio, Loader2 } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

interface S2SResult {
  status: string;
  audio_url: string;
}

const SpeechToSpeechLabPage: React.FC = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioPreview, setAudioPreview] = useState<string | null>(null);
  const [result, setResult] = useState<S2SResult | null>(null);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const mutation = useMutation({
    mutationFn: async (blob: Blob) => {
        const formData = new FormData();
        formData.append('audio_file', blob, 'input_voice.wav');

        return apiClient('/api/v1/labs/s2s/', {
            method: 'POST',
            body: formData,
            headers: {}
        });
    },
    onSuccess: (data) => {
        setResult(data);
    }
  });

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      chunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
        setAudioBlob(blob);
        setAudioPreview(URL.createObjectURL(blob));
        // Auto-submit after recording for fluid feel
        mutation.mutate(blob);
      };

      recorder.start();
      setIsRecording(true);
      setResult(null);
    } catch (err) {
      console.error("Failed to start recording", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  };

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-16 text-center md:text-left">
            <h1 className="text-6xl font-black italic manga-font mb-4 tracking-tighter uppercase">
                SPEECH-TO-SPEECH <span className="text-blue-400 text-glow">LAB</span>
            </h1>
            <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
                Interaction vocale native ultra-basse latence via Kyutai Moshi.
            </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            {/* Control Panel */}
            <div className="space-y-8">
                <Card padding="lg" className="bg-navy-900/40 border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4">
                        {isRecording && <div className="w-3 h-3 bg-red-500 rounded-full animate-ping" />}
                    </div>

                    <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                        <Radio className="w-4 h-4" /> Interface Vocale
                    </h3>

                    <div className="flex flex-col items-center justify-center py-10 space-y-8">
                        <button
                            onClick={isRecording ? stopRecording : startRecording}
                            disabled={mutation.isPending}
                            className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-500 shadow-2xl ${
                                isRecording 
                                ? 'bg-red-500 scale-110 shadow-red-500/40' 
                                : 'bg-blue-500 hover:scale-105 shadow-blue-500/40 hover:bg-blue-600'
                            } ${mutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            {isRecording ? (
                                <Square className="w-12 h-12 text-white fill-current" />
                            ) : (
                                <Mic className="w-12 h-12 text-white" />
                            )}
                        </button>
                        
                        <div className="text-center">
                            <p className="text-sm font-black uppercase tracking-widest mb-2">
                                {isRecording ? "ENREGISTREMENT..." : "CLIQUEZ POUR PARLER"}
                            </p>
                            <p className="text-[10px] font-bold opacity-30 uppercase">L'IA VOUS RÉPONDRA INSTANTANÉMENT</p>
                        </div>
                    </div>
                </Card>

                <Card padding="lg" className="bg-blue-500/10 border-blue-500/20 text-blue-200">
                    <Sparkles className="w-12 h-12 mb-4 opacity-30" />
                    <p className="text-xs font-bold leading-relaxed italic">
                        Le modèle <b>Moshi (v1-preview)</b> est un modèle multimodal natif qui comprend et génère de l'audio directement, sans passer par une transcription textuelle intermédiaire.
                    </p>
                </Card>
            </div>

            {/* Response Area */}
            <div className="lg:col-span-2">
                <div className="bg-black rounded-[4rem] border-4 border-white/5 min-h-[500px] flex flex-col items-center justify-center p-12 relative overflow-hidden shadow-2xl">
                    
                    {/* Decorative Waves */}
                    {isRecording && (
                        <div className="absolute inset-0 flex items-center justify-center opacity-20 pointer-events-none">
                            <div className="flex gap-1 items-end h-32">
                                {[...Array(20)].map((_, i) => (
                                    <div 
                                        key={i} 
                                        className="w-1 bg-blue-400 rounded-full animate-voice-wave" 
                                        style={{ 
                                            height: `${20 + Math.random() * 80}%`,
                                            animationDelay: `${i * 0.05}s`
                                        }} 
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {mutation.isPending && (
                        <div className="text-center space-y-6 animate-fade-in">
                            <Loader2 className="w-16 h-16 text-blue-500 animate-spin mx-auto" />
                            <h2 className="text-2xl font-black italic manga-font uppercase text-glow">Inférence Multimodale...</h2>
                            <p className="text-xs font-bold opacity-40 uppercase tracking-widest">Le cerveau Moshi traite votre signal vocal</p>
                        </div>
                    )}

                    {!isRecording && !mutation.isPending && !result && (
                        <div className="text-center opacity-10">
                            <Volume2 className="w-32 h-32 mx-auto mb-6" />
                            <span className="text-2xl font-black italic manga-font uppercase">Nexus de Communication Inactif</span>
                        </div>
                    )}

                    {result && (
                        <div className="w-full space-y-12 animate-fade-in">
                            <div className="flex flex-col items-center text-center space-y-6">
                                <div className="p-8 bg-blue-500 rounded-full shadow-[0_0_50px_rgba(59,130,246,0.5)]">
                                    <Play className="w-12 h-12 text-white fill-current" />
                                </div>
                                <div>
                                    <Badge variant="primary" className="mb-4">RÉPONSE IA GÉNÉRÉE</Badge>
                                    <h2 className="text-4xl font-black italic manga-font uppercase tracking-tighter">Écoutez le résultat</h2>
                                </div>
                            </div>
                            
                            <div className="bg-white/5 p-8 rounded-[3rem] border border-white/10">
                                <audio src={result.audio_url} autoPlay controls className="w-full h-12" />
                            </div>

                            <Button 
                                onClick={() => setResult(null)} 
                                variant="outline" 
                                fullWidth
                                className="border-white/5 text-white/20 hover:text-white"
                            >
                                RÉINITIALISER LA SESSION
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default SpeechToSpeechLabPage;
