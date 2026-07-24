import React from 'react';
import { ShieldCheck, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';

/** Panneau indigo des engagements éthiques, avec le score de confiance
 *  algorithmique (voix données, en or). */
export const EthicsCommitmentsCard: React.FC<{ ethicsScore: number | null }> = ({
  ethicsScore,
}) => {
  const { t } = useTranslation();
  return (
    <div className="relative flex h-full flex-col justify-between overflow-hidden rounded-2xl border border-[#5D7FD3]/30 bg-[#5D7FD3]/[0.08] p-8 sm:p-10">
      <AlertCircle
        className="absolute -bottom-8 -right-8 h-40 w-40 text-[#5D7FD3]/10"
        aria-hidden="true"
      />
      <div className="relative">
        <h3 className="font-manga mb-8 text-3xl font-black uppercase italic leading-tight tracking-tighter text-[#F4F1E8]">
          {t('social.transparency.ethics_title', 'ENGAGEMENTS ÉTHIQUES')}
        </h3>
        <div className="space-y-6 text-sm font-bold uppercase italic tracking-wider text-[#F4F1E8]/80">
          <p className="flex items-center gap-4">
            <ShieldCheck className="h-5 w-5 flex-none text-[#5D7FD3]" aria-hidden="true" />{' '}
            {t('social.transparency.ethics_1', "Aucune donnée utilisateur n'est revendue.")}
          </p>
          <p className="flex items-center gap-4">
            <ShieldCheck className="h-5 w-5 flex-none text-[#5D7FD3]" aria-hidden="true" />{' '}
            {t('social.transparency.ethics_2', 'Modèles IA prioritairement Open Source.')}
          </p>
          <p className="flex items-center gap-4">
            <ShieldCheck className="h-5 w-5 flex-none text-[#5D7FD3]" aria-hidden="true" />{' '}
            {t('social.transparency.ethics_3', 'Infrastructure 100% transparente.')}
          </p>
        </div>
      </div>
      <div className="relative mt-12 border-t border-[#F4F1E8]/10 pt-8">
        <div className="flex items-end justify-between">
          <span className="text-[10px] font-black uppercase italic tracking-widest text-[#8F94A5]">
            Algorithmic Trust Score
          </span>
          {ethicsScore != null ? (
            <span className="font-manga text-6xl font-black italic leading-none text-[#FDB913]">
              {ethicsScore}%
            </span>
          ) : (
            <span className="text-lg font-black uppercase italic tracking-widest text-[#8F94A5]">
              {t('social.transparency.insufficient_data', 'Données insuffisantes')}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
