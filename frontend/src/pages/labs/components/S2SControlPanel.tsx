import React from 'react';
import { Mic, Square, Radio, Loader2, RefreshCw } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';

export type S2SStatus = 'connecting' | 'ready' | 'recording' | 'thinking' | 'playing' | 'error';

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
  <div className="md:col-span-4 space-y-8">
    <Card
      padding="lg"
      className="bg-navy-900/40 border-white/5 relative overflow-hidden h-full flex flex-col justify-between"
    >
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
          } ${status === 'connecting' || status === 'error' ? 'opacity-30 cursor-not-allowed' : ''}`}
        >
          {isRecording ? (
            <Square className="w-12 h-12 text-white fill-current" />
          ) : (
            <Mic className="w-12 h-12 text-white" />
          )}
        </button>

        <div className="text-center">
          <p className="text-sm font-black uppercase tracking-widest mb-2">
            {status === 'connecting' && 'CONNEXION...'}
            {status === 'ready' && 'CLIQUEZ POUR PARLER'}
            {status === 'recording' && 'ENREGISTREMENT...'}
            {status === 'thinking' && 'RÉPONSE EN COURS...'}
            {status === 'playing' && 'LECTURE DE LA RÉPONSE...'}
            {status === 'error' && 'ERREUR DE CONNEXION'}
          </p>
          <p className="text-[10px] font-bold opacity-30 uppercase">
            {status === 'error' ? errorMessage : 'Flux vocal continu sans latence'}
          </p>
        </div>
      </div>

      {status === 'error' && (
        <Button
          onClick={connectWebSocket}
          variant="outline"
          fullWidth
          className="flex items-center justify-center gap-2"
        >
          <RefreshCw className="w-4 h-4" /> Réessayer
        </Button>
      )}
    </Card>
  </div>
);
