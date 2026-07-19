import React from 'react';
import { Volume2, Loader2, MessageSquare } from 'lucide-react';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import type { S2SStatus } from './S2SControlPanel';

/** Live transcription console: status badge, idle/listening placeholders, the
 *  rolling transcript list, and the reset action. */
export const S2STranscriptConsole: React.FC<{
  status: S2SStatus;
  isRecording: boolean;
  transcripts: string[];
  onReset: () => void;
}> = ({ status, isRecording, transcripts, onReset }) => (
  <div className="md:col-span-8">
    <div className="bg-black rounded-[4rem] border-4 border-white/5 min-h-[400px] flex flex-col p-10 relative overflow-hidden shadow-2xl justify-between h-full">
      {/* Top Status Badge */}
      <div className="flex justify-between items-center w-full mb-6 border-b border-white/5 pb-4">
        <span className="text-xs font-black uppercase tracking-widest opacity-40">
          Transcription en Direct
        </span>
        <Badge variant={status === 'playing' ? 'primary' : 'neutral'}>{status.toUpperCase()}</Badge>
      </div>

      {/* Subtitles / Real-time speech view */}
      <div className="flex-grow flex flex-col justify-center space-y-4 my-4">
        {transcripts.length === 0 && !isRecording && status !== 'playing' && (
          <div className="text-center opacity-10 py-16">
            <Volume2 className="w-24 h-24 mx-auto mb-4" />
            <span className="text-xl font-black italic manga-font uppercase">
              Aucune parole détectée
            </span>
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
              idx === transcripts.length - 1
                ? 'bg-blue-500/10 border border-blue-500/20 text-white scale-100'
                : 'opacity-40 scale-95'
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
          onClick={onReset}
          variant="outline"
          fullWidth
          className="border-white/5 text-white/20 hover:text-white mt-6"
        >
          RÉINITIALISER LA SESSION
        </Button>
      )}
    </div>
  </div>
);
