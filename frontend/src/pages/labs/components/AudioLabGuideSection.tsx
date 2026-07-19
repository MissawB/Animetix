import React from 'react';
import { Mic, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';

/** Static "Guide & Protocole" section at the bottom of the Audio Lab. */
export const AudioLabGuideSection: React.FC = () => {
  const { t } = useTranslation();
  return (
    <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
      <Card
        padding="lg"
        className="bg-white dark:bg-black/40 border-blue-500/20 shadow-[0_0_50px_rgba(59,130,246,0.1)] relative overflow-hidden group"
      >
        <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
          <Mic className="w-64 h-64 text-blue-500" />
        </div>
        <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400" />{' '}
          {t('labs.audio.guide_title', 'Guide de la Forge Vocale')}
        </h4>
        <div className="space-y-4 relative z-10">
          <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
            <span className="text-blue-600 dark:text-blue-400">
              {t('labs.audio.guide_source_title', 'La Source :')}
            </span>{' '}
            {t(
              'labs.audio.guide_source_desc',
              'Choisissez une voix dans le catalogue Seiyuu/VF (clic ou glisser-déposer), ou importez votre propre fichier .wav comme référence.',
            )}
          </p>
          <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
            <span className="text-blue-600 dark:text-blue-400">
              {t('labs.audio.guide_synthesis_title', 'La Synthèse :')}
            </span>{' '}
            {t(
              'labs.audio.guide_synthesis_desc',
              "Tapez un texte (10 à 500 caractères) et lancez la génération : l'IA le lit avec le timbre de la voix choisie, puis vous écoutez le résultat.",
            )}
          </p>
          <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
            <span className="text-blue-600 dark:text-blue-400">
              {t('labs.audio.guide_ingestion_title', "L'Ingestion :")}
            </span>{' '}
            {t(
              'labs.audio.guide_ingestion_desc',
              "Une voix manque au catalogue ? Ajoutez-la via un lien YouTube : l'extrait est téléchargé et transformé en profil vocal réutilisable.",
            )}
          </p>
        </div>
      </Card>

      <div className="p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-black/5 dark:border-white/5 flex flex-col justify-center text-center">
        <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-blue-800/70 dark:text-blue-200/60">
          {t(
            'labs.audio.guide_footer_1',
            'Pipeline de clonage vocal zero-shot : un court échantillon audio de référence suffit pour conditionner la synthèse vocale (TTS), sans entraînement dédié.',
          )}{' '}
          <br />
          {t(
            'labs.audio.guide_footer_2',
            'Les profils du catalogue sont ingérés depuis des extraits YouTube ou des datasets, puis stockés comme échantillons de référence côté serveur.',
          )}
        </p>
      </div>
    </div>
  );
};
