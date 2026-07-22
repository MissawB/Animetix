import React from 'react';
import { Mic2, Sparkles } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';

export const SeiyuuGuideProtocolSection: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="mt-24 grid grid-cols-1 md:grid-cols-2 gap-8">
      <Card
        padding="lg"
        className="bg-black/40 border-emerald-500/20 shadow-[0_0_50px_rgba(16,185,129,0.1)] relative overflow-hidden group"
      >
        <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
          <Mic2 className="w-64 h-64 text-emerald-500" />
        </div>
        <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
          <Sparkles className="w-5 h-5 text-emerald-400" />{' '}
          {t('labs.seiyuu.guide_title', 'Guide des Voix')}
        </h4>
        <div className="space-y-4 relative z-10">
          <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
            <span className="text-emerald-400">
              {t('labs.seiyuu.guide_search_title', 'La Recherche :')}
            </span>{' '}
            {t(
              'labs.seiyuu.guide_search_desc',
              "Tapez le nom d'un doubleur ou d'un personnage, puis filtrez par langue (japonais, français) et par origine du profil.",
            )}
          </p>
          <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
            <span className="text-emerald-400">
              {t('labs.seiyuu.guide_listen_title', "L'Écoute :")}
            </span>{' '}
            {t(
              'labs.seiyuu.guide_listen_desc',
              'Chaque profil contient un échantillon audio. Appuyez sur Play pour vérifier instantanément la signature vocale.',
            )}
          </p>
          <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
            <span className="text-emerald-400">
              {t('labs.seiyuu.guide_ingest_title', "L'Ingestion :")}
            </span>{' '}
            {t(
              'labs.seiyuu.guide_ingest_desc',
              "Ajoutez une nouvelle voix depuis une vidéo YouTube (30 Bx). L'IA extrait, nettoie et indexe l'échantillon pour vous.",
            )}
          </p>
        </div>
      </Card>

      <div className="p-12 rounded-[4rem] bg-gradient-to-br from-emerald-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
        <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-emerald-200/60">
          {t(
            'labs.seiyuu.guide_footer_1',
            'Le catalogue combine un dataset Hugging Face et des voix ingérées depuis YouTube, indexées avec langue, rôles et description.',
          )}{' '}
          <br />
          {t(
            'labs.seiyuu.guide_footer_2',
            "Le pipeline d'ingestion télécharge l'audio, isole la bande vocale (80 Hz – 8 000 Hz) et découpe un échantillon de 10 s sans silence.",
          )}
        </p>
      </div>
    </div>
  );
};
