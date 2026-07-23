import React from 'react';
import { Mic, MicOff, Play, Trash2, Star, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { VoiceProfile } from '../../../types';
import { LAB_BTN_GHOST } from './shared/LabKit';

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
    <div
      role="button"
      tabIndex={0}
      aria-label={t('labs.audio.forge_title', 'Source Vocale')}
      className={`h-fit rounded-2xl border bg-[#0F1016] p-6 transition-colors duration-300 ${
        isDraggingOver ? 'border-[#FDB913] bg-[#FDB913]/5' : 'border-[#F4F1E8]/10'
      }`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <div className="mb-6 flex items-center gap-3">
        <span className="h-4 w-1 flex-none bg-[#E8442B]" aria-hidden />
        <h3 className="font-manga flex items-center gap-2 text-sm font-black uppercase italic tracking-wide text-[#F4F1E8]">
          <Mic className="h-4 w-4" aria-hidden="true" />{' '}
          {t('labs.audio.forge_title', 'Source Vocale')}
        </h3>
        <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
      </div>

      <div className="flex flex-col items-center py-6">
        <button
          onClick={isRecording ? stopRecording : startRecording}
          className={`relative flex h-24 w-24 cursor-pointer items-center justify-center rounded-full border-none transition-all ${
            isRecording
              ? 'animate-pulse bg-[#E8442B] text-[#F4F1E8] scale-110'
              : selectedSeiyuu
                ? 'bg-[#FDB913] text-[#0B0C10]'
                : 'bg-[#F4F1E8] text-[#0B0C10] hover:scale-105'
          }`}
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
            <Star className="w-8 h-8 fill-current" />
          ) : (
            <Mic className="w-8 h-8" />
          )}
        </button>
        <span
          className={`mt-6 text-[9px] font-black uppercase italic tracking-widest ${
            isRecording ? 'text-[#E8442B]' : selectedSeiyuu ? 'text-[#FDB913]' : 'text-[#8F94A5]'
          }`}
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
          <p className="mt-1 text-[7px] font-bold uppercase text-[#8F94A5]">
            {t('labs.audio.recording_drag_note', 'Glissez un autre seiyuu pour changer')}
          </p>
        )}
      </div>

      <div className="relative mb-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-[#F4F1E8]/10"></div>
        </div>
        <div className="relative flex justify-center text-[9px] uppercase font-black">
          <span className="bg-[#0F1016] px-2 text-[#8F94A5]">ou</span>
        </div>
      </div>

      <button
        type="button"
        onClick={() => document.getElementById('audio-upload')?.click()}
        className={`${LAB_BTN_GHOST} w-full justify-center rounded-xl py-3 text-[10px]`}
      >
        {t('labs.audio.recording_import_wav', 'Importer .wav')}
      </button>
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
            className="group flex items-center justify-between rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-3"
          >
            <div className="flex items-center gap-2">
              <div
                className={`flex h-6 w-6 items-center justify-center rounded-lg text-[#0B0C10] ${
                  selectedSeiyuu ? 'bg-[#FDB913]' : 'bg-[#F4F1E8]'
                }`}
              >
                <Play className="w-3 h-3 fill-current" />
              </div>
              <span className="max-w-[80px] truncate text-[9px] font-bold text-[#F4F1E8]">
                {rec.name}
              </span>
            </div>
            <button
              type="button"
              aria-label={t('labs.audio.recording_delete_aria', "Supprimer l'enregistrement")}
              className="cursor-pointer rounded border-none bg-transparent p-1 opacity-0 transition-all hover:bg-[#E8442B]/10 group-hover:opacity-100"
              onClick={onClearRecordings}
            >
              <Trash2 className="w-3 h-3 text-[#E8442B]" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};
