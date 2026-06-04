import React, { useState, useEffect, useRef } from 'react';
import { Mic, Square, Volume2, Sparkles, Radio, Loader2, RefreshCw, MessageSquare } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const SpeechToSpeechLabPage: React.FC = () => {
  const [status, setStatus] = useState<'connecting' | 'ready' | 'recording' | 'thinking' | 'playing' | 'error'>('connecting');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transcripts, setTranscripts] = useState<string[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioQueueRef = useRef<string[]>([]);
  const isPlayingRef = useRef<boolean>(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  // Connect to the WebSocket when page mounts
  useEffect(() => {
    connectWebSocket();
    return () => {
      disconnectWebSocket();
    };
  }, []);

  const connectWebSocket = () => {
    setStatus('connecting');
    setErrorMessage(null);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/labs/s2s/live/`;

    console.log(`Connecting to Gemini Live WebSocket: ${wsUrl}`);
    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      console.log('Gemini Live WebSocket connected');
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('Received from Gemini Live:', data);

        if (data.type === 'session_ready') {
          setStatus('ready');
        } else if (data.type === 'audio_chunk') {
          queueAudioChunk(data.audio);
        } else if (data.type === 'text_chunk') {
          setTranscripts(prev => {
            // Keep only the last few transcripts to avoid overflow
            const newTranscripts = [...prev, data.text];
            if (newTranscripts.length > 5) newTranscripts.shift();
            return newTranscripts;
          });
        } else if (data.type === 'error') {
          setErrorMessage(data.message);
          setStatus('error');
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    socket.onclose = (event) => {
      console.log('Gemini Live WebSocket closed:', event);
      if (status !== 'error') {
        setStatus('connecting');
        // Auto-reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      }
    };

    socket.onerror = (err) => {
      console.error('Gemini Live WebSocket error:', err);
      setErrorMessage('WebSocket connection failed.');
      setStatus('error');
    };
  };

  const disconnectWebSocket = () => {
    stopRecording();
    stopAudioPlayback();
    if (socketRef.current) {
      socketRef.current.close(1000, "Component unmounted");
      socketRef.current = null;
    }
  };

  const startRecording = async () => {
    if (status !== 'ready') return;
    
    stopAudioPlayback(); // Stop any output when user starts speaking
    setTranscripts([]);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // Record in timeslices to stream audio continuously
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = async (e) => {
        if (e.data.size > 0 && socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64Data = (reader.result as string).split(',')[1];
            socketRef.current?.send(JSON.stringify({
              type: 'audio',
              data: base64Data
            }));
          };
          reader.readAsDataURL(e.data);
        }
      };

      // Emit data every 400ms
      recorder.start(400);
      setIsRecording(true);
      setStatus('recording');
    } catch (err) {
      console.error("Failed to start voice capture", err);
      setErrorMessage("Could not access microphone.");
      setStatus('error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      mediaRecorderRef.current = null;
      setIsRecording(false);
      setStatus('thinking');
    }
  };

  // Playback queue management
  const playNextInQueue = () => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setStatus('ready');
      return;
    }
    
    isPlayingRef.current = true;
    setStatus('playing');
    const audioUrl = audioQueueRef.current.shift()!;
    const audio = new Audio(audioUrl);
    currentAudioRef.current = audio;

    audio.onended = () => {
      playNextInQueue();
    };

    audio.onerror = () => {
      console.error("Audio chunk playback error, skipping to next chunk");
      playNextInQueue();
    };

    audio.play().catch(err => {
      console.error("Audio playback failed", err);
      playNextInQueue();
    });
  };

  const queueAudioChunk = (audioB64: string) => {
    const audioUrl = `data:audio/wav;base64,${audioB64}`;
    audioQueueRef.current.push(audioUrl);
    if (!isPlayingRef.current) {
      playNextInQueue();
    }
  };

  const stopAudioPlayback = () => {
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
  };

  return (
    <AnimatedPage>
      <div className="max-w-7xl mx-auto px-6 py-16">
        <header className="mb-16 text-center md:text-left">
          <h1 className="text-6xl font-black italic manga-font mb-4 tracking-tighter uppercase">
            SPEECH-TO-SPEECH <span className="text-blue-400 text-glow">LIVE</span>
          </h1>
          <p className="text-xl font-bold opacity-30 uppercase tracking-[0.3em] max-w-2xl leading-relaxed">
            API Gemini Live bidirectionnelle en temps réel via WebSockets.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Control Panel */}
          <div className="space-y-8">
            <Card padding="lg" className="bg-navy-900/40 border-white/5 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4">
                {isRecording && <div className="w-3 h-3 bg-red-500 rounded-full animate-ping" />}
                {status === 'connecting' && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
              </div>

              <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-widest flex items-center gap-2">
                <Radio className="w-4 h-4" /> Liaison Live Edge
              </h3>

              <div className="flex flex-col items-center justify-center py-10 space-y-8">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={status === 'connecting' || status === 'error'}
                  className={`w-32 h-32 rounded-full flex items-center justify-center transition-all duration-500 shadow-2xl ${
                    isRecording
                      ? 'bg-red-500 scale-110 shadow-red-500/40'
                      : 'bg-blue-500 hover:scale-105 shadow-blue-500/40 hover:bg-blue-600'
                  } ${(status === 'connecting' || status === 'error') ? 'opacity-30 cursor-not-allowed' : ''}`}
                >
                  {isRecording ? (
                    <Square className="w-12 h-12 text-white fill-current" />
                  ) : (
                    <Mic className="w-12 h-12 text-white" />
                  )}
                </button>

                <div className="text-center">
                  <p className="text-sm font-black uppercase tracking-widest mb-2">
                    {status === 'connecting' && "CONNEXION..."}
                    {status === 'ready' && "CLIQUEZ POUR PARLER"}
                    {status === 'recording' && "ENREGISTREMENT EN COURS..."}
                    {status === 'thinking' && "RÉPONSE EN COURS..."}
                    {status === 'playing' && "LECTURE DE LA RÉPONSE..."}
                    {status === 'error' && "ERREUR DE CONNEXION"}
                  </p>
                  <p className="text-[10px] font-bold opacity-30 uppercase">
                    {status === 'error' ? errorMessage : "Flux vocal continu sans latence"}
                  </p>
                </div>
              </div>

              {status === 'error' && (
                <Button onClick={connectWebSocket} variant="outline" fullWidth className="mt-4 flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4" /> Réessayer la connexion
                </Button>
              )}
            </Card>

            <Card padding="lg" className="bg-blue-500/10 border-blue-500/20 text-blue-200">
              <Sparkles className="w-12 h-12 mb-4 opacity-30" />
              <p className="text-xs font-bold leading-relaxed italic">
                L'intégration utilise la <b>Gemini Multimodal Live API</b> pour traiter directement l'audio d'entrée et de sortie sans intermédiaire textuel, éliminant le besoin de serveurs GPU locaux pour le TTS.
              </p>
            </Card>
          </div>

          {/* Response / Transcription Area */}
          <div className="lg:col-span-2">
            <div className="bg-black rounded-[4rem] border-4 border-white/5 min-h-[500px] flex flex-col p-12 relative overflow-hidden shadow-2xl justify-between">
              
              {/* Top Status Badge */}
              <div className="flex justify-between items-center w-full mb-6 border-b border-white/5 pb-4">
                <span className="text-xs font-black uppercase tracking-widest opacity-40">Transcription en Direct</span>
                <Badge variant={status === 'playing' ? 'primary' : 'secondary'}>
                  {status.toUpperCase()}
                </Badge>
              </div>

              {/* Subtitles / Real-time speech view */}
              <div className="flex-1 flex flex-col justify-center space-y-4 my-8">
                {transcripts.length === 0 && !isRecording && status !== 'playing' && (
                  <div className="text-center opacity-10 py-20">
                    <Volume2 className="w-32 h-32 mx-auto mb-6" />
                    <span className="text-2xl font-black italic manga-font uppercase">Aucune parole détectée</span>
                  </div>
                )}

                {isRecording && transcripts.length === 0 && (
                  <div className="text-center space-y-4 opacity-50 py-20">
                    <Loader2 className="w-10 h-10 text-blue-400 animate-spin mx-auto" />
                    <p className="text-sm font-bold uppercase tracking-widest">Écoute en cours...</p>
                  </div>
                )}

                {transcripts.map((text, idx) => (
                  <div 
                    key={idx} 
                    className={`flex items-start gap-4 p-4 rounded-2xl transition-all duration-300 ${
                      idx === transcripts.length - 1 ? 'bg-blue-500/10 border border-blue-500/20 text-white scale-100' : 'opacity-40 scale-95'
                    }`}
                  >
                    <MessageSquare className="w-5 h-5 mt-1 text-blue-400 flex-shrink-0" />
                    <p className="text-sm font-medium leading-relaxed">{text}</p>
                  </div>
                ))}
              </div>

              {/* Reset or Action button */}
              {(transcripts.length > 0 || status === 'playing') && (
                <Button 
                  onClick={() => {
                    stopAudioPlayback();
                    setTranscripts([]);
                    setStatus('ready');
                  }} 
                  variant="outline" 
                  fullWidth
                  className="border-white/5 text-white/20 hover:text-white mt-6"
                >
                  RÉINITIALISER LA SESSION
                </Button>
              )}
            </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default SpeechToSpeechLivePage;
