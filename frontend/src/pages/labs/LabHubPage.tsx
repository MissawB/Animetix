import React from 'react';
import { useTranslation } from 'react-i18next';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { labs, type LabEntry } from './labHubData';
import { type SealInk } from './components/shared/LabKit';
import { SingularityLabCard } from './components/SingularityLabCard';

/** Overrides each entry's title/desc with its i18n translation (falling back to
 *  the bundled French copy), memoised against the active language. */
const useTranslatedLabs = (entries: LabEntry[]): LabEntry[] => {
  const { t } = useTranslation();
  return React.useMemo(
    () =>
      entries.map((lab) => ({
        ...lab,
        title: t(`lab_hub.labs.${lab.id}.title`, lab.title),
        desc: t(`lab_hub.labs.${lab.id}.desc`, lab.desc),
      })),
    [entries, t],
  );
};

/** Indices des « unes » (col-span-2) choisis pour que la grille 3 colonnes
 *  tuile sans trou : (2+1) / (1+2) / (1+1+1) / (2+1). */
const FEATURED_INDICES = new Set([0, 3, 7]);
/** Encres de sceau alternées pour rythmer la grille sur le vide. */
const INK_CYCLE: SealInk[] = ['shu', 'ai', 'kin'];

/** Signature de la page : la singularité — un noyau gravitationnel entouré d'un
 *  disque d'accrétion rotatif (les trois encres d'imprimeur en orbite). */
const SingularityCore: React.FC = () => (
  <div className="relative mx-auto grid h-52 w-52 place-items-center" aria-hidden>
    {/* Disque d'accrétion : dégradé conique en rotation lente. */}
    <div
      className="absolute inset-0 rounded-full opacity-70 blur-[1px] motion-safe:animate-[spin_16s_linear_infinite]"
      style={{
        background:
          'conic-gradient(from 0deg, transparent, rgba(232,68,43,0.55) 12%, transparent 28%, rgba(93,127,211,0.5) 52%, transparent 68%, rgba(253,185,19,0.55) 88%, transparent)',
      }}
    />
    {/* Évidement central : on masque le cœur du disque pour en faire un anneau. */}
    <div className="absolute inset-[13%] rounded-full bg-[#020202]" />
    {/* Halo pulsé du cœur. */}
    <div className="absolute inset-[24%] rounded-full bg-[#E8442B]/25 blur-2xl motion-safe:animate-pulse" />
    {/* Cœur : le sceau de la singularité. */}
    <div className="relative grid h-24 w-24 place-items-center rounded-full border border-[#F4F1E8]/10 bg-[#020202] shadow-[0_0_60px_rgba(232,68,43,0.45)]">
      <span className="font-manga text-2xl font-black italic tracking-tighter text-[#F4F1E8]">
        特異
      </span>
    </div>
  </div>
);

const LabHubPage: React.FC = () => {
  const { t } = useTranslation();
  const translatedLabs = useTranslatedLabs(labs);

  const particles = React.useMemo(
    () =>
      [...Array(22)].map((_, i) => ({
        left: (i * 7) % 100,
        top: (i * 13) % 100,
        duration: 10 + (i % 9),
        delay: i * 0.4,
      })),
    [],
  );

  return (
    <AnimatedPage>
      <div className="relative min-h-screen overflow-hidden bg-[#020202] px-6 py-20 text-[#F4F1E8]">
        {/* Poussière d'étoiles. */}
        <div className="pointer-events-none fixed inset-0 z-0">
          {particles.map((p, i) => (
            <div
              key={i}
              className="particle absolute h-1 w-1 rounded-full bg-white"
              style={{
                left: `${p.left}%`,
                top: `${p.top}%`,
                animationDuration: `${p.duration}s`,
                animationDelay: `${p.delay}s`,
              }}
            />
          ))}
        </div>
        {/* Halos ambiants (shu + indigo cognitif). */}
        <div className="pointer-events-none fixed inset-0 z-0 opacity-[0.12]">
          <div className="absolute left-1/4 top-1/4 h-[500px] w-[500px] rounded-full bg-[#E8442B]/30 blur-[150px]" />
          <div className="absolute bottom-1/4 right-1/4 h-[480px] w-[480px] rounded-full bg-[#5D7FD3]/25 blur-[150px]" />
        </div>

        <div className="relative z-10 mx-auto max-w-7xl">
          {/* Hero : la singularité, puis le titre. */}
          <header className="mb-20 flex flex-col items-center text-center">
            <SingularityCore />
            <p className="mt-8 text-[10px] font-black uppercase tracking-[0.4em] text-[#FDB913]">
              {t('lab_hub.eyebrow', 'Annuaire · Protocoles')}
            </p>
            <h1 className="manga-font mt-3 text-6xl font-black uppercase italic tracking-tighter text-white md:text-7xl">
              Singularity{' '}
              <span className="text-[#E8442B] drop-shadow-[0_0_18px_rgba(232,68,43,0.5)]">
                Labs
              </span>
            </h1>
            <p className="mt-5 max-w-2xl text-base leading-relaxed text-white/50">
              {t(
                'lab_hub.subtitle',
                "Explorez la frontière entre l'IA générative et la cognition pure.",
              )}
            </p>
          </header>

          {/* Les protocoles, en cartes vitrées sur le vide. */}
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {translatedLabs.map((lab, idx) => (
              <SingularityLabCard
                key={lab.id}
                lab={lab}
                index={idx}
                featured={FEATURED_INDICES.has(idx)}
                ink={INK_CYCLE[idx % INK_CYCLE.length]}
              />
            ))}
          </div>

          <footer className="mt-24 border-t border-white/10 pt-12 text-center">
            <p className="mx-auto max-w-3xl text-sm leading-relaxed text-white/55">
              {t(
                'lab_hub.footer_1',
                "Les Singularity Labs regroupent les fonctionnalités expérimentales d'Animetix : des outils d'IA générative et cognitive appliqués à l'univers anime & manga.",
              )}{' '}
              <br />
              {t(
                'lab_hub.footer_2',
                'Génération de lore, doublage et synthèse vocale, analyse vidéo, reconstruction 3D, moteurs de raisonnement — chaque module est un prototype de recherche en évolution constante.',
              )}
            </p>
          </footer>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default LabHubPage;
