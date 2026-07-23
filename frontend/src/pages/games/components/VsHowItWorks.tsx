import React from 'react';
import { useTranslation } from 'react-i18next';
import { Swords } from 'lucide-react';

export const VsHowItWorks: React.FC = () => {
  const { t } = useTranslation();
  const steps = [
    {
      t: t('games.vs_battle.step1_title', 'Choisis ton premier combattant'),
      d: t(
        'games.vs_battle.step1_desc',
        'Sélectionne un personnage dans le roster : il prend la place A.',
      ),
    },
    {
      t: t('games.vs_battle.step2_title', 'Désigne l’adversaire'),
      d: t(
        'games.vs_battle.step2_desc',
        'Filtre le roster par nom de personnage ou par franchise, puis remplis la place B.',
      ),
    },
    {
      t: t('games.vs_battle.step3_title', 'Engage le duel'),
      d: t(
        'games.vs_battle.step3_desc',
        'L’IA confronte le lore, les pouvoirs et les hauts faits des deux camps.',
      ),
    },
    {
      t: t('games.vs_battle.step4_title', 'Découvre le verdict'),
      d: t(
        'games.vs_battle.step4_desc',
        'Le vainqueur et son résumé s’affichent, puis le combat rejoint l’arène publique.',
      ),
    },
  ];

  return (
    <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 md:p-12">
      <div className="mb-10 flex items-center gap-4">
        <span className="h-6 w-1.5 flex-none bg-[#E8442B]" aria-hidden />
        <h2 className="font-manga text-xl md:text-2xl font-black italic uppercase tracking-wide text-[#F4F1E8]">
          {t('games.vs_battle.how_title', "Comment fonctionne l'Arène")}
        </h2>
        <span
          className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]/60"
          aria-hidden
        >
          手順
        </span>
        <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
      </div>
      <p className="mb-8 -mt-6 text-sm text-[#8F94A5]">
        {t('games.vs_battle.how_subtitle', "Un arbitre IA tranche n'importe quel duel")}
      </p>

      <ol className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-6 max-w-3xl">
        {steps.map((step, i) => (
          <li key={step.t} className="flex gap-5">
            <span
              className="font-manga flex-none text-2xl font-black italic leading-none text-[#E8442B]"
              aria-hidden
            >
              {String(i + 1).padStart(2, '0')}
            </span>
            <div>
              <p className="text-xs font-black uppercase tracking-widest text-[#F4F1E8]">
                {step.t}
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-[#8F94A5]">{step.d}</p>
            </div>
          </li>
        ))}
      </ol>

      <p className="mt-10 flex items-center gap-2 text-[11px] font-black uppercase tracking-widest text-[#FDB913]">
        <Swords className="w-3.5 h-3.5" aria-hidden="true" />{' '}
        {t(
          'games.vs_battle.tip',
          "Astuce : tu peux opposer un personnage à lui-même — c'est un match miroir.",
        )}
      </p>
    </section>
  );
};
