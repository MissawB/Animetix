import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Mic,
  Square,
  Volume2,
  Radio,
  Loader2,
  RefreshCw,
  MessageSquare,
  Search,
  User,
  Star,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { apiClient } from "../../utils/apiClient";
import { VoiceProfile } from '../../types';

const SpeechToSpeechLabPage: React.FC = () => {
  const [status, setStatus] = useState<'connecting' | 'ready' | 'recording' | 'thinking' | 'playing' | 'error'>('connecting');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transcripts, setTranscripts] = useState<string[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  // Selected voice profile for post-processing voice cloning
  const [selectedProfile, setSelectedProfile] = useState<VoiceProfile | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [langFilter, setLangFilter] = useState('');

  // Fetch Voice Profiles
  const { data: profilesData, isLoading: isLoadingProfiles } = useQuery<{ results: VoiceProfile[] }>({
    queryKey: ['voice-profiles-s2s', searchQuery, langFilter],
    queryFn: () => {
      let url = `/api/v1/labs/audio/seiyuu/?q=${encodeURIComponent(searchQuery)}`;
      if (langFilter) url += `&language=${langFilter}`;
      return apiClient(url);
    },
  });

  const socketRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioQueueRef = useRef<string[]>([]);
  const isPlayingRef = useRef<boolean>(false);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

  const playNextInQueueRef = useRef<() => void>(() => {});
  const connectWebSocketRef = useRef<() => void>(() => {});

  const stopAudioPlayback = useCallback(() => {
    audioQueueRef.current = [];
    isPlayingRef.current = false;
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
  }, []);

  const playNextInQueue = useCallback(() => {
    if (audioQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      setStatus(prev => prev === 'playing' ? 'ready' : prev);
      return;
    }

    isPlayingRef.current = true;
    setStatus('playing');
    const nextUrl = audioQueueRef.current.shift()!;
    const audio = new Audio(nextUrl);
    currentAudioRef.current = audio;

    audio.onended = () => {
      playNextInQueueRef.current();
    };

    audio.play().catch(err => {
      console.error('Audio playback failed:', err);
      playNextInQueueRef.current();
    });
  }, []);

  useEffect(() => {
    playNextInQueueRef.current = playNextInQueue;
  }, [playNextInQueue]);

  const queueAudioChunk = useCallback((audioB64: string) => {
    const audioUrl = `data:audio/wav;base64,${audioB64}`;
    audioQueueRef.current.push(audioUrl);
    if (!isPlayingRef.current) {
      playNextInQueue();
    }
  }, [playNextInQueue]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      mediaRecorderRef.current = null;
      setIsRecording(false);
      setStatus('thinking');
    }
  }, []);

  const connectWebSocket = useCallback(() => {
    setStatus('connecting');
    setErrorMessage(null);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    let wsUrl = `${protocol}//${host}/ws/labs/s2s/live/`;
    if (selectedProfile) {
      wsUrl += `?voice_profile_id=${selectedProfile.id}`;
    }

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
          setStatus('thinking');
          setTranscripts(prev => {
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
        // Auto-reconnect after 3 seconds
        setTimeout(() => {
          if (socketRef.current === socket) {
            connectWebSocketRef.current();
          }
        }, 3000);
      }
    };

    socket.onerror = (err) => {
      console.error('Gemini Live WebSocket error:', err);
      setErrorMessage('WebSocket connection failed.');
      setStatus('error');
    };
  }, [status, queueAudioChunk, selectedProfile]);

  useEffect(() => {
    connectWebSocketRef.current = connectWebSocket;
  }, [connectWebSocket]);

  const disconnectWebSocket = useCallback(() => {
    stopRecording();
    stopAudioPlayback();
    if (socketRef.current) {
      socketRef.current.close(1000, "Component unmounted/reconnecting");
      socketRef.current = null;
    }
  }, [stopRecording, stopAudioPlayback]);

  // Connect to the WebSocket when page mounts or profile changes
  useEffect(() => {
    const timer = setTimeout(() => {
      connectWebSocket();
    }, 100);

    return () => {
      clearTimeout(timer);
      disconnectWebSocket();
    };
  }, [connectWebSocket, disconnectWebSocket]);

  const startRecording = async () => {
    if (status !== 'ready') return;

    stopAudioPlayback();
    setTranscripts([]);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
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

      recorder.start(400);
      setIsRecording(true);
      setStatus('recording');
    } catch (err) {
      console.error("Failed to start voice capture", err);
      setErrorMessage("Could not access microphone.");
      setStatus('error');
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
            API Gemini Live bidirectionnelle en temps réel clonée via RVC v2.
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Casting Panel (Left Sidebar) */}
          <Card padding="lg" className="lg:col-span-4 h-fit bg-gray-900/40 border-white/5 shadow-2xl space-y-6">
            <div>
              <h3 className="text-xs font-black uppercase opacity-40 mb-4 tracking-widest flex items-center gap-2">
                <User className="w-4 h-4" /> Casting Persona
              </h3>
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                Sélectionnez une voix pour cloner la réponse de l'IA en temps réel.
              </p>
            </div>

            {/* Language filter tab */}
            <div className="flex gap-1 bg-black/40 p-1 rounded-xl border border-white/5">
              {[
                { label: 'Tous', value: '' },
                { label: 'Seiyuu (JP)', value: 'japanese' },
                { label: 'VF (FR)', value: 'french' }
              ].map(opt => (
                <button
                  key={opt.value}
                  onClick={() => setLangFilter(opt.value)}
                  className={`flex-1 py-2 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all ${
                    langFilter === opt.value
                      ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                      : 'text-white/40 hover:text-white border border-transparent'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                placeholder="Rechercher une voix..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-black/40 border border-white/5 rounded-xl pl-10 pr-4 py-3 font-bold text-xs outline-none focus:border-blue-500/50"
              />
            </div>

            {/* Profiles List */}
            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">
              {/* Default Option (No profile) */}
              <button
                onClick={() => setSelectedProfile(null)}
                className={`w-full px-4 py-3 rounded-xl text-left text-xs font-black transition-all border flex items-center justify-between group ${
                  selectedProfile === null
                    ? 'border-blue-500 bg-blue-500/10 text-white shadow-lg'
                    : 'border-white/5 bg-black/25 text-white/50 hover:border-white/10 hover:text-white'
                }`}
              >
                <div className="flex flex-col gap-0.5 truncate">
                  <span>Gemini Native Voice</span>
                  <span className="text-[8px] opacity-40 font-medium uppercase tracking-wide">
                    Sans post-clonage RVC
                  </span>
                </div>
                <Badge variant="neutral" className="text-[7px] font-black uppercase bg-black/40">
                  ⚡ DEFAULT
                </Badge>
              </button>

              {isLoadingProfiles ? (
                <div className="py-10 text-center">
                  <Loader2 className="w-6 h-6 animate-spin mx-auto text-blue-500" />
                </div>
              ) : profilesData?.results && profilesData.results.length > 0 ? (
                profilesData.results.map((p) => (
                  <button
                    key={p.id}
                    onClick={() => setSelectedProfile(p)}
                    className={`w-full px-4 py-3 rounded-xl text-left text-xs font-black transition-all border flex items-center justify-between group ${
                      selectedProfile?.id === p.id
                        ? 'border-blue-500 bg-blue-500/10 text-white shadow-lg'
                        : 'border-white/5 bg-black/25 text-white/50 hover:border-white/10 hover:text-white'
                    }`}
                  >
                    <div className="flex flex-col gap-0.5 truncate pr-2">
                      <span className="truncate">{p.name}</span>
                      <span className="text-[8px] opacity-40 truncate font-medium uppercase tracking-wide">
                        {p.roles || 'Doubleur'}
                      </span>
                    </div>
                    <Badge variant="neutral" className="text-[7px] font-black uppercase shrink-0 bg-black/40">
                      {p.language === 'japanese' ? '🇯🇵 JP' : p.language === 'french' ? '🇫🇷 FR' : '🌐'}
                    </Badge>
                  </button>
                ))
              ) : (
                <div className="py-10 text-center text-white/20">
                  <span className="text-[10px] font-black uppercase">Aucune voix trouvée</span>
                </div>
              )}
            </div>

            {selectedProfile && (
              <Card padding="md" className="bg-blue-500/10 border-blue-500/20 text-blue-200 space-y-2">
                <span className="text-[8px] font-black uppercase tracking-wider text-blue-400 flex items-center gap-1">
                  <Star className="w-3 h-3 fill-current text-blue-400" /> Acteur Actif
                </span>
                <h4 className="font-black text-sm uppercase">{selectedProfile.name}</h4>
                <p className="text-[10px] opacity-60 leading-relaxed italic">
                  "{selectedProfile.definition || 'Profil vocal configuré pour le doublage conversationnel.'}"
                </p>
              </Card>
            )}
          </Card>

          {/* S2S Main Console (Right) */}
          <div className="lg:col-span-8 space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
              {/* Control Panel */}
              <div className="md:col-span-4 space-y-8">
                <Card padding="lg" className="bg-navy-900/40 border-white/5 relative overflow-hidden h-full flex flex-col justify-between">
                  <div className="absolute top-0 right-0 p-4">
                    {isRecording && <div className="w-3 h-3 bg-red-500 rounded-full animate-ping" />}
                    {status === 'connecting' && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
                  </div>

                  <h3 className="text-xs font-black uppercase opacity-40 tracking-widest flex items-center gap-2">
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
                        {status === 'recording' && "ENREGISTREMENT..."}
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
                    <Button onClick={connectWebSocket} variant="outline" fullWidth className="flex items-center justify-center gap-2">
                      <RefreshCw className="w-4 h-4" /> Réessayer
                    </Button>
                  )}
                </Card>
              </div>

              {/* Response / Transcription Area */}
              <div className="md:col-span-8">
                <div className="bg-black rounded-[4rem] border-4 border-white/5 min-h-[400px] flex flex-col p-10 relative overflow-hidden shadow-2xl justify-between h-full">

                  {/* Top Status Badge */}
                  <div className="flex justify-between items-center w-full mb-6 border-b border-white/5 pb-4">
                    <span className="text-xs font-black uppercase tracking-widest opacity-40">Transcription en Direct</span>
                    <Badge variant={status === 'playing' ? 'primary' : 'neutral'}>
                      {status.toUpperCase()}
                    </Badge>
                  </div>

                  {/* Subtitles / Real-time speech view */}
                  <div className="flex-grow flex flex-col justify-center space-y-4 my-4">
                    {transcripts.length === 0 && !isRecording && status !== 'playing' && (
                      <div className="text-center opacity-10 py-16">
                        <Volume2 className="w-24 h-24 mx-auto mb-4" />
                        <span className="text-xl font-black italic manga-font uppercase">Aucune parole détectée</span>
                      </div>
                    )}

                    {isRecording && transcripts.length === 0 && (
                      <div className="text-center space-y-4 opacity-50 py-16">
                        <Loader2 className="w-8 h-8 text-blue-400 animate-spin mx-auto" />
                        <p className="text-xs font-bold uppercase tracking-widest">Écoute en cours...</p>
                      </div>
                    )}

                    {transcripts.map((text, idx) => (
                      <div
                        key={idx}
                        className={`flex items-start gap-4 p-4 rounded-2xl transition-all duration-300 ${
                          idx === transcripts.length - 1 ? 'bg-blue-500/10 border border-blue-500/20 text-white scale-100' : 'opacity-40 scale-95'
                        }`}
                      >
                        <MessageSquare className="w-4 h-4 mt-1 text-blue-400 flex-shrink-0" />
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
        </div>
      </div>
    </AnimatedPage>
  );
};

export default SpeechToSpeechLabPage;
