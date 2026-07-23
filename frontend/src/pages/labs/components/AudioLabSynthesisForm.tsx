import React from 'react';
import { Save, Play } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { UseFormRegister, UseFormHandleSubmit, FieldErrors } from 'react-hook-form';
import { VoiceProfile } from '../../../types';
import { LabPanel, LAB_INPUT, LAB_CTA } from './shared/LabKit';

export type AudioFormValues = { text: string };

/** The "Forge Vocale" text-to-speech form plus the ready-result banner. Form
 *  state is owned by the parent (react-hook-form) and threaded in as props. */
export const AudioLabSynthesisForm: React.FC<{
  register: UseFormRegister<AudioFormValues>;
  handleSubmit: UseFormHandleSubmit<AudioFormValues>;
  errors: FieldErrors<AudioFormValues>;
  onSubmit: (values: AudioFormValues) => void | Promise<void>;
  selectedSeiyuu: VoiceProfile | null;
  disabled: boolean;
  audioUrl?: string;
  playResult: () => void;
}> = ({
  register,
  handleSubmit,
  errors,
  onSubmit,
  selectedSeiyuu,
  disabled,
  audioUrl,
  playResult,
}) => {
  const { t } = useTranslation();
  return (
    <>
      <LabPanel>
        <div className="mb-6 flex items-center gap-3">
          <span className="h-4 w-1 flex-none bg-[#E8442B]" aria-hidden />
          <h3 className="font-manga text-xl font-black uppercase italic tracking-wide text-[#F4F1E8]">
            {t('labs.audio.forge_title', 'Forge')}{' '}
            <span className="text-[#E8442B]">{t('labs.audio.forge_title_accent', 'vocale')}</span>
          </h3>
          <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-8">
          <div className="flex flex-col gap-2">
            <textarea
              {...register('text')}
              className={`${LAB_INPUT} min-h-[200px] resize-none text-base ${
                errors.text ? 'border-[#E8442B]' : ''
              }`}
              placeholder={
                selectedSeiyuu
                  ? t('labs.audio.forge_synthesize_with_name', {
                      name: selectedSeiyuu.name,
                      defaultValue: 'Faites parler {{name}}...',
                    })
                  : t(
                      'labs.audio.recording_import_aria',
                      "Tapez le texte que l'IA doit dire avec votre voix...",
                    )
              }
            ></textarea>
            {errors.text && (
              <span className="pl-4 text-xs font-black text-[#E8442B]">{errors.text.message}</span>
            )}
          </div>

          <button type="submit" disabled={disabled} className={LAB_CTA}>
            <Save className="h-5 w-5" aria-hidden="true" />{' '}
            {selectedSeiyuu
              ? t('labs.audio.forge_synthesize_with_name', {
                  name: selectedSeiyuu.name,
                  defaultValue: 'Synthétiser {{name}}',
                })
              : t('labs.audio.generate')}
          </button>
        </form>
      </LabPanel>

      {audioUrl && (
        <div className="flex items-center justify-between rounded-2xl border border-[#FDB913]/30 bg-[#FDB913]/[0.06] p-8 animate-slide-up">
          <div>
            <h4 className="mb-1 font-manga text-xl font-black uppercase italic leading-none text-[#FDB913]">
              {t('labs.audio.result_ready', 'Résultat prêt')}
            </h4>
            <p className="text-sm font-bold text-[#8F94A5]">
              {t('labs.audio.result_success', 'Votre voix a été synthétisée avec succès.')}
            </p>
          </div>
          <button
            type="button"
            onClick={playResult}
            aria-label={t('labs.audio.result_play_aria', 'Écouter le résultat')}
            className="cursor-pointer rounded-xl border-none bg-[#FDB913] p-4 text-[#0B0C10] transition-colors hover:bg-[#e0a70f]"
          >
            <Play className="w-6 h-6 fill-current" />
          </button>
        </div>
      )}
    </>
  );
};
