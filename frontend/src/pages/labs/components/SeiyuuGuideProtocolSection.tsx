import React from 'react';
import { useTranslation } from 'react-i18next';
import { LabGuide } from './shared/LabKit';

export const SeiyuuGuideProtocolSection: React.FC = () => {
  const { t } = useTranslation();

  return (
    <LabGuide
      steps={[
        {
          title: 'La recherche',
          body: t(
            'labs.seiyuu.guide_search_desc',
            "Tapez le nom d'un doubleur ou d'un personnage, puis filtrez par langue (japonais, français) et par origine du profil.",
          ),
        },
        {
          title: "L'écoute",
          body: t(
            'labs.seiyuu.guide_listen_desc',
            'Chaque profil contient un échantillon audio. Appuyez sur Play pour vérifier instantanément la signature vocale.',
          ),
        },
        {
          title: "L'ingestion",
          body: t(
            'labs.seiyuu.guide_ingest_desc',
            "Ajoutez une nouvelle voix depuis une vidéo YouTube (30 Bx). L'IA extrait, nettoie et indexe l'échantillon pour vous.",
          ),
        },
      ]}
      note={`${t(
        'labs.seiyuu.guide_footer_1',
        'Le catalogue combine un dataset Hugging Face et des voix ingérées depuis YouTube, indexées avec langue, rôles et description.',
      )} ${t(
        'labs.seiyuu.guide_footer_2',
        "Le pipeline d'ingestion télécharge l'audio, isole la bande vocale (80 Hz – 8 000 Hz) et découpe un échantillon de 10 s sans silence.",
      )}`}
    />
  );
};
