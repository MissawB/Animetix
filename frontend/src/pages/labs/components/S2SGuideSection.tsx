import React from 'react';
import { LabGuide } from './shared/LabKit';

/** "Guide du Live" section at the bottom of the Speech-to-Speech page. */
export const S2SGuideSection: React.FC = () => (
  <LabGuide
    steps={[
      {
        title: 'Choisis une voix',
        body: 'Dans le panneau de casting, sélectionne un seiyuu ou un doubleur VF — ou reste sur la voix native de Gemini.',
      },
      {
        title: 'Parle au micro',
        body: "Clique sur le micro, parle, puis arrête l'enregistrement : l'IA t'écoute et te répond à voix haute, comme au téléphone.",
      },
      {
        title: 'Suis la conversation',
        body: "La réponse est lue en audio pendant que sa transcription s'affiche en direct dans la console, pour suivre l'échange à l'écrit.",
      },
    ]}
    note="Guide du Live : l'audio du micro est streamé en chunks base64 vers l'API Gemini Live par WebSocket, et la réponse revient en flux (texte + audio). Si un profil vocal est sélectionné, la sortie passe par une conversion voix-à-voix RVC pour cloner le timbre choisi avant lecture."
  />
);
