import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { apiClient } from '../../utils/apiClient';
import { auth } from '../../utils/firebase';
import { useAuthStore } from '../../store/authStore';
import { VoiceProfile } from '../../types';
import { logger } from '../../utils/logger';
import { S2SCastingSidebar } from './components/S2SCastingSidebar';
import { S2SControlPanel, type S2SStatus } from './components/S2SControlPanel';
import { S2STranscriptConsole } from './components/S2STranscriptConsole';
import { S2SGuideSection } from './components/S2SGuideSection';

const SpeechToSpeechLabPage: React.FC = () => {
  const [status, setStatus] = useState<S2SStatus>('connecting');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [transcripts, setTranscripts] = useState<string[]>([]);
  const [isRecording, setIsRecording] = useState(false);

  // Selected voice profile for post-processing voice cloning
  const [selectedProfile, setSelectedProfile] = useState<VoiceProfile | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [langFilter, setLangFilter] = useState('');

  // Fetch Voice Profiles
  const { data: profilesData, isLoading: isLoadingProfiles } = useQuery<{
    results: VoiceProfile[];
  }>({
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
      setStatus((prev) => (prev === 'playing' ? 'ready' : prev));
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

    audio.play().catch((err) => {
      console.error('Audio playback failed:', err);
      playNextInQueueRef.current();
    });
  }, []);

  useEffect(() => {
    playNextInQueueRef.current = playNextInQueue;
  }, [playNextInQueue]);

  const queueAudioChunk = useCallback(
    (audioB64: string) => {
      const audioUrl = `data:audio/wav;base64,${audioB64}`;
      audioQueueRef.current.push(audioUrl);
      if (!isPlayingRef.current) {
        playNextInQueue();
      }
    },
    [playNextInQueue],
  );

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
      mediaRecorderRef.current = null;
      setIsRecording(false);
      setStatus('thinking');
    }
  }, []);

  const connectWebSocket = useCallback(async () => {
    setStatus('connecting');
    setErrorMessage(null);

    // Session S2S Live = GPU (Gemini Live) : requiert login + coûte des Berrix.
    // On gate avant d'ouvrir le socket plutôt que d'encaisser un close 4401 brut.
    if (!useAuthStore.getState().isAuthenticated) {
      setErrorMessage("Connexion requise : ce mode utilise l'IA (GPU) et coûte des Berrix.");
      setStatus('error');
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const params = new URLSearchParams();
    if (selectedProfile) {
      params.set('voice_profile_id', String(selectedProfile.id));
    }
    const qs = params.toString();
    const wsUrl = `${protocol}//${host}/ws/labs/s2s/live/${qs ? `?${qs}` : ''}`;

    // Le token Firebase voyage via Sec-WebSocket-Protocol (["bearer", token]),
    // PAS dans l'URL : un token en query string finirait dans les logs d'accès.
    // Le middleware WS lit aussi la session côté serveur si présente.
    let token: string | undefined;
    try {
      token = await auth.currentUser?.getIdToken();
    } catch (err) {
      logger.log('Failed to get Firebase ID token for S2S WS', err);
    }

    logger.log(`Connecting to Gemini Live WebSocket: ${wsUrl}`);
    const socket = token ? new WebSocket(wsUrl, ['bearer', token]) : new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      logger.log('Gemini Live WebSocket connected');
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        logger.log('Received from Gemini Live:', data);

        if (data.type === 'session_ready') {
          setStatus('ready');
        } else if (data.type === 'audio_chunk') {
          queueAudioChunk(data.audio);
        } else if (data.type === 'text_chunk') {
          setStatus('thinking');
          setTranscripts((prev) => {
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
      logger.log('Gemini Live WebSocket closed:', event);
      // Auth (4401) / solde insuffisant (4402) / durée max (4408) : ne pas boucler.
      if (event.code === 4401 || event.code === 4402 || event.code === 4408) {
        setErrorMessage(
          event.code === 4402
            ? 'Berrix insuffisants pour une session Speech-to-Speech.'
            : event.code === 4408
              ? 'Session terminée (durée maximale atteinte).'
              : 'Connexion requise pour ce mode IA (GPU).',
        );
        setStatus('error');
        return;
      }
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
      socketRef.current.close(1000, 'Component unmounted/reconnecting');
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
        if (
          e.data.size > 0 &&
          socketRef.current &&
          socketRef.current.readyState === WebSocket.OPEN
        ) {
          const reader = new FileReader();
          reader.onloadend = () => {
            const base64Data = (reader.result as string).split(',')[1];
            socketRef.current?.send(
              JSON.stringify({
                type: 'audio',
                data: base64Data,
              }),
            );
          };
          reader.readAsDataURL(e.data);
        }
      };

      recorder.start(400);
      setIsRecording(true);
      setStatus('recording');
    } catch (err) {
      console.error('Failed to start voice capture', err);
      setErrorMessage('Could not access microphone.');
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
          <S2SCastingSidebar
            profilesData={profilesData}
            isLoadingProfiles={isLoadingProfiles}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            langFilter={langFilter}
            setLangFilter={setLangFilter}
            selectedProfile={selectedProfile}
            setSelectedProfile={setSelectedProfile}
          />

          {/* S2S Main Console (Right) */}
          <div className="lg:col-span-8 space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
              <S2SControlPanel
                status={status}
                isRecording={isRecording}
                errorMessage={errorMessage}
                startRecording={startRecording}
                stopRecording={stopRecording}
                connectWebSocket={connectWebSocket}
              />

              <S2STranscriptConsole
                status={status}
                isRecording={isRecording}
                transcripts={transcripts}
                onReset={() => {
                  stopAudioPlayback();
                  setTranscripts([]);
                  setStatus('ready');
                }}
              />
            </div>
          </div>
        </div>

        {/* Guide & Protocole */}
        <S2SGuideSection />
      </div>
    </AnimatedPage>
  );
};

export default SpeechToSpeechLabPage;
