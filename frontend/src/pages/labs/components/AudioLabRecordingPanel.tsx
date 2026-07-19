import React from 'react';
import { Mic, MicOff, Play, Trash2, Star, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { VoiceProfile } from '../../../types';

export interface Recording {
  id: number;
  name: string;
  duration: string;
}

/** Voice-source panel: record toggle, .wav import, and the recordings list. It
 *  is also the drop target for seiyuu cards, so the drag handlers are wired by
 *  the parent (which owns the selection state). */
export const AudioLabRecordingPanel: React.FC<{
  isRecording: boolean;
  selectedSeiyuu: VoiceProfile | null;
  audioLoading: string | null;
  recordings: Recording[];
  startRecording: () => void;
  stopRecording: () => void;
  onFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onDragOver: (e: React.DragEvent) => void;
  onDragLeave: () => void;
  onDrop: (e: React.DragEvent) => void;
  onClearRecordings: () => void;
  isDraggingOver: boolean;
}> = ({
  isRecording,
  selectedSeiyuu,
  audioLoading,
  recordings,
  startRecording,
  stopRecording,
  onFileChange,
  onDragOver,
  onDragLeave,
  onDrop,
  onClearRecordings,
  isDraggingOver,
}) => {
  const { t } = useTranslation();
  return (
    <Card
      padding="lg"
      className={`h-fit transition-all duration-300 ${isDraggingOver ? 'ring-4 ring-blue-500 bg-blue-500/10 scale-105' : ''}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <h3 className="text-xs font-black uppercase opacity-40 mb-8 tracking-[0.2em] flex items-center gap-2">
        <Mic className="w-4 h-4" /> {t('labs.audio.forge_title', 'Source Vocale')}
      </h3>

      <div className="flex flex-col items-center py-6">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`w-24 h-24 rounded-full flex items-center justify-center transition-all shadow-2xl relative ${isRecording ? 'bg-red-500 animate-pulse scale-110' : selectedSeiyuu ? 'bg-blue-600 text-white' : 'bg-black text-white hover:scale-105'}`}
          aria-label={
            isRecording
              ? t('labs.audio.recording_stop_aria', "Arrêter l'enregistrement")
              : t('labs.audio.recording_start_aria', "Démarrer l'enregistrement")
          }
        >
          {audioLoading ? (
            <Loader2 className="w-8 h-8 animate-spin" />
          ) : isRecording ? (
            <MicOff className="w-8 h-8" />
          ) : selectedSeiyuu ? (
            <Star className="w-8 h-8 fill-current text-yellow-400" />
          ) : (
            <Mic className="w-8 h-8" />
          )}
        </button>
        <span
          className={`mt-6 font-black italic uppercase tracking-widest text-[9px] ${isRecording ? 'text-red-500' : selectedSeiyuu ? 'text-blue-500' : 'opacity-40'}`}
        >
          {audioLoading
            ? t('labs.audio.recording_loading_voice', 'Chargement voix...')
            : isRecording
              ? t('labs.audio.recording_recording_status', 'Enregistrement...')
              : selectedSeiyuu
                ? t('labs.audio.recording_voice_label', {
                    name: selectedSeiyuu.name,
                    defaultValue: 'Voix: {{name}}',
                  })
                : t('labs.audio.recording_ready_status', 'Prêt à enregistrer')}
        </span>
        {selectedSeiyuu && (
          <p className="text-[7px] font-bold uppercase opacity-30 mt-1">
            {t('labs.audio.recording_drag_note', 'Glissez un autre seiyuu pour changer')}
          </p>
        )}
      </div>

      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-black/5 dark:border-white/5"></div>
        </div>
        <div className="relative flex justify-center text-[9px] uppercase font-black">
          <span className="px-2 bg-white dark:bg-navy-800 text-gray-400">ou</span>
        </div>
      </div>

      <Button
        variant="outline"
        fullWidth
        onClick={() => document.getElementById('audio-upload')?.click()}
        className="text-[10px] py-3"
      >
        {t('labs.audio.recording_import_wav', 'Importer .wav')}
      </Button>
      <input
        type="file"
        id="audio-upload"
        className="hidden"
        accept=".wav,.mp3"
        onChange={onFileChange}
        aria-label={t('labs.audio.recording_import_aria', 'Importer un fichier audio')}
      />

      <div className="mt-8 space-y-3">
        {recordings.map((rec) => (
          <div
            key={rec.id}
            className="p-3 bg-gray-50 dark:bg-gray-800 rounded-xl flex items-center justify-between group"
          >
            <div className="flex items-center gap-2">
              <div
                className={`w-6 h-6 rounded-lg flex items-center justify-center text-white ${selectedSeiyuu ? 'bg-blue-600' : 'bg-blue-500'}`}
              >
                <Play className="w-3 h-3 fill-current" />
              </div>
              <span className="font-bold text-[9px] truncate max-w-[80px]">{rec.name}</span>
            </div>
            <button
              type="button"
              aria-label={t('labs.audio.recording_delete_aria', "Supprimer l'enregistrement")}
              className="p-1 hover:bg-red-500/10 rounded transition-all opacity-0 group-hover:opacity-100 border-none bg-transparent cursor-pointer"
              onClick={onClearRecordings}
            >
              <Trash2 className="w-3 h-3 text-red-500" />
            </button>
          </div>
        ))}
      </div>
    </Card>
  );
};
