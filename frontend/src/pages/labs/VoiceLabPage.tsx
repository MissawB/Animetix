import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Mic, 
  Upload, 
  Settings, 
  Volume2,
  Zap,
  CheckCircle,
  AlertCircle,
  ChevronRight
} from 'lucide-react';
import { WaveformVisualizer } from '../../features/labs/components/WaveformVisualizer';
import { useVoiceCloning } from '../../features/labs/hooks/useVoiceCloning';

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
        const file = new File([blob], "recording.wav", { type: 'audio/wav' });
        setAudioFile(file);
        s.getTracks().forEach(track => track.stop());
        setStream(null);
      };

      mediaRecorder.start();
    } catch (err) {
      console.error("Error accessing microphone:", err);
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
    <div className="min-h-screen bg-black text-white p-8">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="max-w-7xl mx-auto"
      >
        <header className="mb-12 flex items-center justify-between">
          <div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
              Voice Lab
            </h1>
            <p className="text-zinc-400 mt-2 text-lg">Next-generation RVC voice cloning and synthesis.</p>
          </div>
          <div className="p-4 bg-zinc-900/50 rounded-2xl border border-zinc-800">
            <Settings className="w-6 h-6 text-zinc-500 hover:text-white transition-colors cursor-pointer" />
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Side: Source */}
          <section className="space-y-6">
            <div className="p-8 bg-zinc-900/30 rounded-3xl border border-zinc-800/50 backdrop-blur-xl">
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <Volume2 className="text-red-500" />
                Source Audio
              </h2>

              <div className="aspect-video bg-zinc-950 rounded-2xl border border-dashed border-zinc-800 flex flex-col items-center justify-center relative overflow-hidden">
                <WaveformVisualizer stream={stream} isActive={isRecording} />
                
                {!isRecording && !audioFile && (
                  <div className="text-center p-6">
                    <div className="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-red-500/20">
                      <Mic className="text-red-500 w-8 h-8" />
                    </div>
                    <p className="text-zinc-400">Record or upload a reference voice</p>
                  </div>
                )}

                {audioFile && !isRecording && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="text-center">
                      <p className="text-red-500 font-medium mb-2">{audioFile.name}</p>
                      <button 
                        onClick={() => setAudioFile(null)}
                        className="text-xs text-zinc-500 hover:text-white underline"
                      >
                        Remove file
                      </button>
                    </div>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4 mt-6">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`flex items-center justify-center gap-3 p-4 rounded-2xl font-bold transition-all ${
                    isRecording 
                      ? 'bg-red-500 text-white animate-pulse' 
                      : 'bg-zinc-800 text-zinc-300 hover:bg-zinc-700'
                  }`}
                >
                  <Mic className="w-5 h-5" />
                  {isRecording ? 'Stop Recording' : 'Start Recording'}
                </button>
                
                <label 
                  htmlFor="audio-upload"
                  className="flex items-center justify-center gap-3 p-4 bg-zinc-800 text-zinc-300 rounded-2xl font-bold cursor-pointer hover:bg-zinc-700 transition-all border border-zinc-700"
                >
                  <Upload className="w-5 h-5" />
                  Upload File
                  <input id="audio-upload" type="file" accept="audio/*" onChange={handleFileUpload} className="hidden" />
                </label>
              </div>
            </div>
          </section>

          {/* Right Side: Synthesis */}
          <section className="space-y-6">
            <div className="p-8 bg-zinc-900/30 rounded-3xl border border-zinc-800/50 backdrop-blur-xl">
              <h2 className="text-2xl font-semibold mb-6 flex items-center gap-3">
                <Zap className="text-orange-500" />
                Synthesis Settings
              </h2>

              <div className="space-y-6">
                <div>
                  <label htmlFor="target-text" className="text-sm font-medium text-zinc-500 mb-2 block uppercase tracking-wider">Target Text</label>
                  <textarea
                    id="target-text"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Enter text to synthesize..."
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-2xl p-4 h-32 focus:border-red-500 transition-all resize-none outline-none text-zinc-200"
                  />
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label htmlFor="model-select" className="text-sm font-medium text-zinc-500 mb-2 block uppercase tracking-wider">Model Selection</label>
                    <select id="model-select" className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 outline-none text-zinc-300 focus:border-red-500">
                      <option>RVC-v2 Default</option>
                      <option>HuggingFace Model X</option>
                    </select>
                  </div>
                  <div>
                    <label htmlFor="index-rate" className="text-sm font-medium text-zinc-500 mb-2 block uppercase tracking-wider">Index Rate</label>
                    <select id="index-rate" className="w-full bg-zinc-950 border border-zinc-800 rounded-xl p-3 outline-none text-zinc-300 focus:border-red-500">
                      <option>0.75 (Recommended)</option>
                      <option>0.50 (Natural)</option>
                      <option>1.00 (Precise)</option>
                    </select>
                  </div>
                </div>

                <div>
                  <div className="flex justify-between mb-2">
                    <label htmlFor="pitch-shift" className="text-sm font-medium text-zinc-500 uppercase tracking-wider">Pitch Shift</label>
                    <span className="text-orange-500 font-bold">{pitch > 0 ? `+${pitch}` : pitch} semitones</span>
                  </div>
                  <input
                    id="pitch-shift"
                    type="range"
                    min="-12"
                    max="12"
                    value={pitch}
                    onChange={(e) => setPitch(parseInt(e.target.value))}
                    className="w-full accent-orange-500 bg-zinc-800 rounded-lg h-2"
                  />
                  <div className="flex justify-between mt-1 text-[10px] text-zinc-600 font-bold">
                    <span>-12</span>
                    <span>0</span>
                    <span>+12</span>
                  </div>
                </div>

                <button
                  onClick={handleClone}
                  disabled={loading || !audioFile || !text}
                  className={`w-full p-5 rounded-2xl font-black text-xl flex items-center justify-center gap-3 transition-all ${
                    loading 
                      ? 'bg-zinc-800 text-zinc-500 cursor-not-allowed' 
                      : 'bg-gradient-to-r from-red-600 to-orange-600 hover:scale-[1.02] active:scale-95 shadow-lg shadow-red-900/20'
                  }`}
                >
                  {loading ? (
                    <div className="w-6 h-6 border-2 border-zinc-500 border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      Synthesize
                      <ChevronRight className="w-6 h-6" />
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Result Area */}
            <AnimatePresence>
              {(result || error) && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className={`p-6 rounded-3xl border ${
                    error ? 'bg-red-500/5 border-red-500/20' : 'bg-green-500/5 border-green-500/20'
                  }`}
                >
                  {error ? (
                    <div className="flex items-center gap-4 text-red-500">
                      <AlertCircle className="w-8 h-8" />
                      <div>
                        <h3 className="font-bold">Synthesis Failed</h3>
                        <p className="text-sm opacity-80">Check server logs for details.</p>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 text-green-500">
                        <CheckCircle className="w-8 h-8" />
                        <div>
                          <h3 className="font-bold">Synthesis Ready</h3>
                          <p className="text-sm opacity-80">Download or preview below</p>
                        </div>
                      </div>
                      <audio controls className="h-10 accent-green-500" src={result?.audio_data}>
                        <track kind="captions" />
                      </audio>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </section>
        </div>
      </motion.div>
    </div>
  );
};

export default VoiceLabPage;
