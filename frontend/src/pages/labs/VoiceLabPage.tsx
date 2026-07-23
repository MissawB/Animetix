import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Upload, Zap, CheckCircle, AlertCircle, ChevronRight } from 'lucide-react';
import { WaveformVisualizer } from '../../features/labs/components/WaveformVisualizer';
import { useVoiceCloning } from '../../features/labs/hooks/useVoiceCloning';
import {
  LabPage,
  LabHeader,
  LabPanel,
  LabGuide,
  LAB_INPUT,
  LAB_LABEL,
  LAB_CTA,
  LAB_BTN_GHOST,
} from './components/shared/LabKit';

const VoiceLabPage: React.FC = () => {
  const [text, setText] = useState('');
  const [pitch, setPitch] = useState(0);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const { clone, loading, result, error } = useVoiceCloning();

  const startRecording = async () => {
    try {
      const s = await navigator.mediaDevices.getUserMedia({ audio: true });
      setStream(s);
      setIsRecording(true);
      const mediaRecorder = new MediaRecorder(s);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
        const file = new File([blob], 'recording.wav', { type: 'audio/wav' });
        setAudioFile(file);
        s.getTracks().forEach((track) => track.stop());
        setStream(null);
      };

      mediaRecorder.start();
    } catch (err) {
      console.error('Error accessing microphone:', err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setAudioFile(e.target.files[0]);
    }
  };

  const handleClone = async () => {
    if (!audioFile || !text) return;
    await clone({ text, audioFile, pitch });
  };

  return (
    <LabPage>
      <LabHeader
        code="Protocole · Voice"
        title="Clonage"
        accent="vocal"
        lede="Enregistre ou importe une voix de référence, écris un texte, et le moteur RVC le prononce avec ce timbre. Le pitch et le taux d'index se règlent avant la synthèse."
      />

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Left Side: Source */}
        <section className="space-y-6">
          <LabPanel title="Source audio">
            <div className="relative flex aspect-video flex-col items-center justify-center overflow-hidden rounded-xl border border-dashed border-[#F4F1E8]/15 bg-[#0B0C10]">
              <WaveformVisualizer stream={stream} isActive={isRecording} />

              {!isRecording && !audioFile && (
                <div className="p-6 text-center">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-[#E8442B]/25 bg-[#E8442B]/10">
                    <Mic className="h-8 w-8 text-[#E8442B]" aria-hidden="true" />
                  </div>
                  <p className="text-sm text-[#8F94A5]">
                    Enregistre ou importe une voix de référence
                  </p>
                </div>
              )}

              {audioFile && !isRecording && (
                <div className="absolute inset-0 flex items-center justify-center bg-[#0B0C10]/80 backdrop-blur-sm">
                  <div className="text-center">
                    <p className="mb-2 font-medium text-[#FDB913]">{audioFile.name}</p>
                    <button
                      onClick={() => setAudioFile(null)}
                      className="cursor-pointer border-none bg-transparent text-xs text-[#8F94A5] underline hover:text-[#F4F1E8]"
                    >
                      Retirer le fichier
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 grid grid-cols-2 gap-4">
              <button
                onClick={isRecording ? stopRecording : startRecording}
                className={
                  isRecording
                    ? 'inline-flex cursor-pointer animate-pulse items-center justify-center gap-2 rounded-xl border-none bg-[#E8442B] p-4 text-xs font-black uppercase tracking-widest text-[#F4F1E8] transition-colors'
                    : `${LAB_BTN_GHOST} justify-center rounded-xl p-4`
                }
              >
                <Mic className="h-4 w-4" aria-hidden="true" />
                {isRecording ? "Arrêter l'enregistrement" : "Démarrer l'enregistrement"}
              </button>

              <label
                htmlFor="audio-upload"
                className={`${LAB_BTN_GHOST} justify-center rounded-xl p-4`}
              >
                <Upload className="h-4 w-4" aria-hidden="true" />
                Importer un fichier
                <input
                  id="audio-upload"
                  aria-label="Importer un fichier audio"
                  type="file"
                  accept="audio/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
            </div>
          </LabPanel>
        </section>

        {/* Right Side: Synthesis */}
        <section className="space-y-6">
          <LabPanel
            title="Réglages de synthèse"
            corner={
              <span className="flex items-center gap-1.5">
                <Zap className="h-3.5 w-3.5" aria-hidden="true" /> RVC v2
              </span>
            }
          >
            <div className="space-y-6">
              <div>
                <label htmlFor="target-text" className={`${LAB_LABEL} mb-2 block`}>
                  Texte cible
                </label>
                <textarea
                  id="target-text"
                  aria-label="Texte cible à synthétiser"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  placeholder="Écris le texte à synthétiser…"
                  className={`${LAB_INPUT} h-32 resize-none`}
                />
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label htmlFor="model-select" className={`${LAB_LABEL} mb-2 block`}>
                    Modèle
                  </label>
                  <select id="model-select" className={LAB_INPUT}>
                    <option>RVC-v2 Default</option>
                    <option>HuggingFace Model X</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="index-rate" className={`${LAB_LABEL} mb-2 block`}>
                    Taux d'index
                  </label>
                  <select id="index-rate" className={LAB_INPUT}>
                    <option>0.75 (recommandé)</option>
                    <option>0.50 (naturel)</option>
                    <option>1.00 (précis)</option>
                  </select>
                </div>
              </div>

              <div>
                <div className="mb-2 flex justify-between">
                  <label htmlFor="pitch-shift" className={LAB_LABEL}>
                    Décalage de hauteur
                  </label>
                  <span className="text-xs font-black text-[#FDB913]">
                    {pitch > 0 ? `+${pitch}` : pitch} demi-tons
                  </span>
                </div>
                <input
                  id="pitch-shift"
                  aria-label="Décalage de hauteur (pitch)"
                  type="range"
                  min="-12"
                  max="12"
                  value={pitch}
                  onChange={(e) => setPitch(parseInt(e.target.value))}
                  className="h-2 w-full rounded-lg bg-[#F4F1E8]/10 accent-[#FDB913]"
                />
                <div className="mt-1 flex justify-between text-[10px] font-bold text-[#8F94A5]">
                  <span>-12</span>
                  <span>0</span>
                  <span>+12</span>
                </div>
              </div>

              <button
                onClick={handleClone}
                disabled={loading || !audioFile || !text}
                className={LAB_CTA}
              >
                {loading ? (
                  <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#F4F1E8]/50 border-t-transparent" />
                ) : (
                  <>
                    Synthétiser
                    <ChevronRight className="h-5 w-5" aria-hidden="true" />
                  </>
                )}
              </button>
            </div>
          </LabPanel>

          {/* Result Area */}
          <AnimatePresence>
            {(result || error) && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className={`rounded-2xl border p-6 ${
                  error
                    ? 'border-[#E8442B]/30 bg-[#E8442B]/[0.06]'
                    : 'border-[#FDB913]/30 bg-[#FDB913]/[0.06]'
                }`}
              >
                {error ? (
                  <div className="flex items-center gap-4 text-[#E8442B]">
                    <AlertCircle className="h-8 w-8" aria-hidden="true" />
                    <div>
                      <h3 className="font-bold">Échec de la synthèse</h3>
                      <p className="text-sm text-[#8F94A5]">
                        Consulte les journaux du serveur pour le détail.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 text-[#FDB913]">
                      <CheckCircle className="h-8 w-8" aria-hidden="true" />
                      <div>
                        <h3 className="font-bold">Synthèse prête</h3>
                        <p className="text-sm text-[#8F94A5]">Écoute le résultat ci-contre</p>
                      </div>
                    </div>
                    <audio
                      controls
                      aria-label="Audio synthétisé"
                      className="h-10"
                      src={result?.audio_data}
                    >
                      <track kind="captions" />
                    </audio>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </section>
      </div>

      <LabGuide
        steps={[
          {
            title: 'La référence',
            body: 'Enregistre ta voix au micro ou importe un fichier audio. Cet extrait sert de modèle de timbre pour la synthèse.',
          },
          {
            title: 'Le texte',
            body: "Écris ce que la voix doit dire, puis clique sur Synthétiser : l'IA prononce ton texte avec la voix de référence.",
          },
          {
            title: 'Les réglages',
            body: "Le décalage de hauteur monte ou descend la voix (par demi-tons) et le taux d'index dose la fidélité au timbre d'origine.",
          },
        ]}
        note="Conversion vocale basée RVC v2 (Retrieval-based Voice Conversion) : le texte est d'abord synthétisé (TTS), puis le timbre est converti vers la voix de référence. Le pitch est appliqué en demi-tons et le taux d'index contrôle le poids de la récupération des caractéristiques du locuteur cible."
      />
    </LabPage>
  );
};

export default VoiceLabPage;
