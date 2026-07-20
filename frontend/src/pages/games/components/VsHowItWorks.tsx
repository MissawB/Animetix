import React from 'react';
import { useTranslation } from 'react-i18next';
import { Flame, Swords } from 'lucide-react';

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
    <section className="rounded-[2.5rem] border-2 border-red-600/30 bg-gradient-to-br from-red-950/40 via-navy-900 to-navy-900 p-8 md:p-12">
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-red-600/20 text-red-500 mb-4">
          <Flame className="w-7 h-7" />
        </div>
        <h2 className="text-2xl md:text-3xl font-black italic manga-font uppercase text-white">
          {t('games.vs_battle.how_title', "Comment fonctionne l'Arène")}
        </h2>
        <p className="text-sm font-bold opacity-50 uppercase tracking-[0.25em] mt-2">
          {t('games.vs_battle.how_subtitle', "Un arbitre IA tranche n'importe quel duel")}
        </p>
      </div>

      <ol className="grid grid-cols-1 sm:grid-cols-2 gap-5 max-w-3xl mx-auto">
        {steps.map((step, i) => (
          <li key={step.t} className="flex gap-4 p-4 rounded-2xl bg-black/30 border border-white/5">
            <span className="shrink-0 w-9 h-9 rounded-xl bg-red-600 text-white grid place-items-center font-black italic">
              {i + 1}
            </span>
            <div>
              <p className="font-black uppercase italic text-sm text-white leading-tight">
                {step.t}
              </p>
              <p className="text-xs font-medium opacity-55 leading-snug mt-1">{step.d}</p>
            </div>
          </li>
        ))}
      </ol>

      <p className="text-center text-[11px] font-black uppercase tracking-widest text-fuchsia-400/80 mt-8 flex items-center justify-center gap-2">
        <Swords className="w-3.5 h-3.5" />{' '}
        {t(
          'games.vs_battle.tip',
          "Astuce : tu peux opposer un personnage à lui-même — c'est un match miroir.",
        )}
      </p>
    </section>
  );
};
