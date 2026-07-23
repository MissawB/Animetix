import React from 'react';
import { Volume2, Loader2, MessageSquare } from 'lucide-react';
import { LAB_BTN_GHOST } from './shared/LabKit';
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
    <div className="flex h-full min-h-[400px] flex-col justify-between rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-8">
      {/* Top status row */}
      <div className="mb-6 flex w-full items-center justify-between border-b border-[#F4F1E8]/10 pb-4">
        <span className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
          Transcription en Direct
        </span>
        <span
          className={`text-[10px] font-black uppercase tracking-widest ${
            status === 'playing' ? 'text-[#FDB913]' : 'text-[#8F94A5]'
          }`}
        >
          {status}
        </span>
      </div>

      {/* Subtitles / Real-time speech view */}
      <div className="my-4 flex flex-grow flex-col justify-center space-y-4">
        {transcripts.length === 0 && !isRecording && status !== 'playing' && (
          <div className="py-16 text-center">
            <Volume2 className="mx-auto mb-4 h-16 w-16 text-[#8F94A5]/40" aria-hidden="true" />
            <span className="font-manga block text-xl font-black uppercase italic text-[#F4F1E8]/60">
              Aucune parole détectée
            </span>
          </div>
        )}

        {isRecording && transcripts.length === 0 && (
          <div className="space-y-4 py-16 text-center">
            <Loader2 className="mx-auto h-8 w-8 animate-spin text-[#FDB913]" aria-hidden="true" />
            <p className="text-xs font-black uppercase tracking-widest text-[#8F94A5]">
              Écoute en cours…
            </p>
          </div>
        )}

        {transcripts.map((text, idx) => (
          <div
            key={idx}
            className={`flex items-start gap-4 rounded-xl p-4 transition-colors duration-300 ${
              idx === transcripts.length - 1
                ? 'border border-[#FDB913]/25 bg-[#FDB913]/[0.06] text-[#F4F1E8]'
                : 'text-[#8F94A5]'
            }`}
          >
            <MessageSquare
              className="mt-1 h-4 w-4 flex-shrink-0 text-[#FDB913]"
              aria-hidden="true"
            />
            <p className="text-sm font-medium leading-relaxed">{text}</p>
          </div>
        ))}
      </div>

      {/* Reset action */}
      {(transcripts.length > 0 || status === 'playing') && (
        <button
          type="button"
          onClick={onReset}
          className={`${LAB_BTN_GHOST} mt-6 w-full justify-center`}
        >
          Réinitialiser la session
        </button>
      )}
    </div>
  </div>
);
