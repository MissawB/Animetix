import React from 'react';
import { Radio, Sparkles } from 'lucide-react';
import { Card } from '../../../components/ui/Card';

/** Static "Guide du Live" section at the bottom of the Speech-to-Speech page. */
export const S2SGuideSection: React.FC = () => (
  <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
    <Card
      padding="lg"
      className="bg-white dark:bg-black/40 border-blue-500/20 shadow-[0_0_50px_rgba(59,130,246,0.1)] relative overflow-hidden group"
    >
      <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
        <Radio className="w-64 h-64 text-blue-500" />
      </div>
      <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
        <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400" /> Guide du Live
      </h4>
      <div className="space-y-4 relative z-10">
        <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
          <span className="text-blue-600 dark:text-blue-400">La Conversation :</span> Cliquez sur le
          micro, parlez, puis relâchez : l'IA vous écoute et vous répond à voix haute, comme un
          appel téléphonique.
        </p>
        <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
          <span className="text-blue-600 dark:text-blue-400">Le Casting :</span> Choisissez une voix
          dans le panneau de gauche pour que la réponse de l'IA soit prononcée avec le timbre d'un
          seiyuu ou d'un doubleur VF.
        </p>
        <p className="text-xs font-bold uppercase tracking-wider text-black/60 dark:text-white/60 leading-relaxed">
          <span className="text-blue-600 dark:text-blue-400">La Transcription :</span> Le texte de
          la réponse s'affiche en direct pendant la lecture audio, pour suivre la conversation à
          l'écrit.
        </p>
      </div>
    </Card>

    <div className="p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-black/5 dark:border-white/5 flex flex-col justify-center text-center">
      <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-blue-800/70 dark:text-blue-200/60">
        Liaison WebSocket bidirectionnelle vers l'API Gemini Live : l'audio du micro est streamé en
        chunks base64, la réponse revient en flux (texte + audio). <br />
        Si un profil vocal est sélectionné, la sortie passe par une étape de conversion voix-à-voix
        RVC pour cloner le timbre choisi avant lecture.
      </p>
    </div>
  </div>
);
