import React from 'react';
import { Save, Play, Wand2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { UseFormRegister, UseFormHandleSubmit, FieldErrors } from 'react-hook-form';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { VoiceProfile } from '../../../types';

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
      <Card padding="lg" className="relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-5">
          <Wand2 className="w-40 h-42 text-purple-500" />
        </div>

        <h3 className="text-3xl font-black italic manga-font mb-8">
          {t('labs.audio.forge_title', 'FORGE')}{' '}
          <span className="text-purple-500">{t('labs.audio.forge_title_accent', 'VOCALE')}</span>
        </h3>

        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-8">
          <div className="flex flex-col gap-2">
            <textarea
              {...register('text')}
              className={`w-full p-8 rounded-[2rem] bg-gray-50 dark:bg-gray-800 outline-none font-medium text-lg min-h-[200px] transition-all
                                        ${errors.text ? 'ring-2 ring-red-500' : 'focus:ring-2 focus:ring-purple-500'}
                                    `}
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
              <span className="text-red-500 text-xs font-black pl-4">{errors.text.message}</span>
            )}
          </div>

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            disabled={disabled}
            className="bg-gradient-to-r from-purple-600 to-blue-600 border-none py-6 animate-pulse"
          >
            <Save className="w-6 h-6 mr-2" />{' '}
            {selectedSeiyuu
              ? t('labs.audio.forge_synthesize_with_name', {
                  name: selectedSeiyuu.name,
                  defaultValue: 'Synthétiser {{name}}',
                })
              : t('labs.audio.generate')}
          </Button>
        </form>
      </Card>

      {audioUrl && (
        <div className="bg-green-500/10 border-2 border-green-500 p-8 rounded-[2.5rem] flex items-center justify-between animate-slide-up">
          <div>
            <h4 className="font-black text-green-500 italic text-xl uppercase leading-none mb-1">
              {t('labs.audio.result_ready', 'RÉSULTAT PRÊT !')}
            </h4>
            <p className="font-bold opacity-60 text-sm">
              {t('labs.audio.result_success', 'Votre voix a été synthétisée avec succès.')}
            </p>
          </div>
          <Button variant="success" className="p-4 rounded-2xl" onClick={playResult}>
            <Play className="w-6 h-6 fill-current" />
          </Button>
        </div>
      )}
    </>
  );
};
