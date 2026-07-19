import React from 'react';
import { ShieldCheck, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Card } from '../../../components/ui/Card';

/** Blue "ethical commitments" panel with the algorithmic trust score. */
export const EthicsCommitmentsCard: React.FC<{ ethicsScore: number | null }> = ({
  ethicsScore,
}) => {
  const { t } = useTranslation();
  return (
    // !important : sinon le bg-surface-card du composant Card gagne sur bg-blue-600.
    <Card
      padding="lg"
      className="!bg-blue-600 text-white border-none relative overflow-hidden flex flex-col justify-between h-full shadow-blue-600/20 rounded-[3rem]"
    >
      <AlertCircle className="w-40 h-40 absolute -right-8 -bottom-8 opacity-10" />
      <div>
        <h3 className="text-4xl font-black italic manga-font mb-8 leading-tight uppercase tracking-tighter">
          {t('social.transparency.ethics_title', 'ENGAGEMENTS ÉTHIQUES')}
        </h3>
        <div className="space-y-6 opacity-90 font-bold text-sm italic uppercase tracking-wider">
          <p className="flex items-center gap-4">
            <ShieldCheck className="w-5 h-5 text-blue-200" />{' '}
            {t('social.transparency.ethics_1', "Aucune donnée utilisateur n'est revendue.")}
          </p>
          <p className="flex items-center gap-4">
            <ShieldCheck className="w-5 h-5 text-blue-200" />{' '}
            {t('social.transparency.ethics_2', 'Modèles IA prioritairement Open Source.')}
          </p>
          <p className="flex items-center gap-4">
            <ShieldCheck className="w-5 h-5 text-blue-200" />{' '}
            {t('social.transparency.ethics_3', 'Infrastructure 100% transparente.')}
          </p>
        </div>
      </div>
      <div className="mt-12 pt-8 border-t border-white/20">
        <div className="flex justify-between items-end">
          <span className="text-[10px] font-black uppercase tracking-widest opacity-60 italic">
            Algorithmic Trust Score
          </span>
          {ethicsScore != null ? (
            <span className="text-7xl font-black italic manga-font leading-none drop-shadow-lg">
              {ethicsScore}%
            </span>
          ) : (
            <span className="text-lg font-black italic uppercase tracking-widest opacity-70">
              {t('social.transparency.insufficient_data', 'Données insuffisantes')}
            </span>
          )}
        </div>
      </div>
    </Card>
  );
};
