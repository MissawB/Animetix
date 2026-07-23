import React from 'react';
import { Mic, Square, Loader2, RefreshCw } from 'lucide-react';
import { LabPanel, LAB_BTN_GHOST } from './shared/LabKit';

export type S2SStatus = 'connecting' | 'ready' | 'recording' | 'thinking' | 'playing' | 'error';

const STATUS_LABELS: Record<S2SStatus, string> = {
  connecting: 'Connexion…',
  ready: 'Clique pour parler',
  recording: 'Enregistrement…',
  thinking: 'Réponse en cours…',
  playing: 'Lecture de la réponse…',
  error: 'Erreur de connexion',
};

/** Live-link control panel: the record/stop button, status text, and the
 *  retry button shown on error. All behaviour is owned by the page's session
 *  logic and passed in as callbacks. */
export const S2SControlPanel: React.FC<{
  status: S2SStatus;
  isRecording: boolean;
  errorMessage: string | null;
  startRecording: () => void;
  stopRecording: () => void;
  connectWebSocket: () => void;
}> = ({ status, isRecording, errorMessage, startRecording, stopRecording, connectWebSocket }) => (
  <div className="md:col-span-4">
    <LabPanel
      title="Liaison live"
      className="flex h-full flex-col justify-between"
      corner={
        status === 'connecting' ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden="true" />
        ) : isRecording ? (
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 animate-ping rounded-full bg-[#E8442B]" aria-hidden /> rec
          </span>
        ) : undefined
      }
    >
      <div className="flex flex-col items-center justify-center gap-8 py-10">
        <button
          type="button"
          onClick={isRecording ? stopRecording : startRecording}
          disabled={status === 'connecting' || status === 'error'}
          aria-label={isRecording ? "Arrêter l'enregistrement" : 'Parler au micro'}
          className={`flex h-32 w-32 cursor-pointer items-center justify-center rounded-full border-none transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
            isRecording
              ? 'bg-[#FDB913] text-[#0B0C10]'
              : 'bg-[#E8442B] text-[#F4F1E8] hover:bg-[#c93a24]'
          }`}
        >
          {isRecording ? (
            <Square className="h-12 w-12 fill-current" aria-hidden="true" />
          ) : (
            <Mic className="h-12 w-12" aria-hidden="true" />
          )}
        </button>

        <div className="text-center">
          <p className="font-manga text-base font-black uppercase italic tracking-wide text-[#F4F1E8]">
            {STATUS_LABELS[status]}
          </p>
          <p className="mt-2 text-xs leading-relaxed text-[#8F94A5]">
            {status === 'error' ? errorMessage : 'Flux vocal continu, faible latence.'}
          </p>
        </div>
      </div>

      {status === 'error' && (
        <button
          type="button"
          onClick={connectWebSocket}
          className={`${LAB_BTN_GHOST} w-full justify-center`}
        >
          <RefreshCw className="h-4 w-4" aria-hidden="true" /> Réessayer
        </button>
      )}
    </LabPanel>
  </div>
);
