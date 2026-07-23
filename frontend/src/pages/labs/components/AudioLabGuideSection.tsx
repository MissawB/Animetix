import React from 'react';
import { useTranslation } from 'react-i18next';
import { LabGuide } from './shared/LabKit';

/** Static "Guide & Protocole" section at the bottom of the Audio Lab. */
export const AudioLabGuideSection: React.FC = () => {
  const { t } = useTranslation();
  return (
    <LabGuide
      steps={[
        {
          title: t('labs.audio.guide_source_title', 'La source'),
          body: t(
            'labs.audio.guide_source_desc',
            'Choisissez une voix dans le catalogue Seiyuu/VF (clic ou glisser-déposer), ou importez votre propre fichier .wav comme référence.',
          ),
        },
        {
          title: t('labs.audio.guide_synthesis_title', 'La synthèse'),
          body: t(
            'labs.audio.guide_synthesis_desc',
            "Tapez un texte (10 à 500 caractères) et lancez la génération : l'IA le lit avec le timbre de la voix choisie, puis vous écoutez le résultat.",
          ),
        },
        {
          title: t('labs.audio.guide_ingestion_title', "L'ingestion"),
          body: t(
            'labs.audio.guide_ingestion_desc',
            "Une voix manque au catalogue ? Ajoutez-la via un lien YouTube : l'extrait est téléchargé et transformé en profil vocal réutilisable.",
          ),
        },
      ]}
      note={`${t('labs.audio.guide_title', 'Guide de la Forge Vocale')} — ${t(
        'labs.audio.guide_footer_1',
        'Pipeline de clonage vocal zero-shot : un court échantillon audio de référence suffit pour conditionner la synthèse vocale (TTS), sans entraînement dédié.',
      )} ${t(
        'labs.audio.guide_footer_2',
        'Les profils du catalogue sont ingérés depuis des extraits YouTube ou des datasets, puis stockés comme échantillons de référence côté serveur.',
      )}`}
    />
  );
};
