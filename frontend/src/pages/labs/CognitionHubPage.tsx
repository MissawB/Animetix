import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

/** Les trois synapses du noyau cognitif — une encre d'imprimeur chacune. */
const MODULES = [
  {
    id: 'archetype',
    title: 'Archetype Nexus',
    sub: 'Convergence synaptique',
    desc: "Visualisez votre position dans l'espace latent des fans et la convergence de vos traits psychographiques.",
    url: '/social/archetype-nexus/',
    glyph: '型',
    hex: '#5D7FD3',
    /* position desktop dans la constellation (en %) */
    x: 18,
    y: 22,
    float: 5,
  },
  {
    id: 'memory',
    title: 'Neuro-Memory',
    sub: 'Empreinte sémantique',
    desc: "Gérez l'empreinte sémantique que vous laissez sur l'IA et auditez vos vecteurs de préférence en temps réel.",
    url: '/social/neuro-memory/',
    glyph: '憶',
    hex: '#FDB913',
    x: 68,
    y: 14,
    float: 6.5,
  },
  {
    id: 'simulator',
    title: 'Counterfactual Simulator',
    sub: 'Optimisation de timeline',
    desc: 'Explorez les mondes possibles de vos interactions et calculez le regret contrefactuel minimum.',
    url: '/search/counterfactual/',
    glyph: '時',
    hex: '#E8442B',
    x: 42,
    y: 60,
    float: 5.8,
  },
] as const;

/** Une synapse : nœud lumineux flottant + cartouche, navigation directe. */
const SynapseNode: React.FC<{
  module: (typeof MODULES)[number];
  desc: string;
  className?: string;
  style?: React.CSSProperties;
}> = ({ module, desc, className = '', style }) => (
  <motion.div
    animate={{ y: [0, -12, 0] }}
    transition={{ repeat: Infinity, duration: module.float, ease: 'easeInOut' }}
    className={className}
    style={style}
  >
    <Link
      to={module.url}
      className="group flex w-56 flex-col items-center text-center no-underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-8 focus-visible:outline-[#FDB913]"
    >
      <span className="relative mb-6 flex h-32 w-32 items-center justify-center">
        <span
          aria-hidden
          className="absolute inset-0 rounded-full opacity-25 blur-[36px] transition-opacity duration-500 group-hover:opacity-60"
          style={{ backgroundColor: module.hex }}
        />
        <span
          className="relative flex h-full w-full items-center justify-center rounded-full border-2 bg-[#020202]/80 text-5xl font-bold leading-none transition-transform duration-500 group-hover:scale-110"
          style={{ borderColor: `${module.hex}66`, color: module.hex }}
          aria-hidden
        >
          {module.glyph}
        </span>
      </span>
      <p
        className="mb-1 text-[10px] font-black uppercase tracking-widest"
        style={{ color: module.hex }}
      >
        {module.sub}
      </p>
      <h2 className="font-manga text-2xl font-black uppercase italic leading-none text-white">
        {module.title}
      </h2>
      <p className="mt-3 text-[11px] leading-relaxed text-white/40 opacity-0 transition-opacity duration-500 group-hover:opacity-100">
        {desc}
      </p>
    </Link>
  </motion.div>
);

const CognitionHubPage: React.FC = () => {
  const { t } = useTranslation();

  const particleConfig = useMemo(
    () =>
      [...Array(24)].map((_, i) => ({
        left: (i * 11) % 100,
        top: (i * 17) % 100,
        duration: 9 + (i % 8),
        delay: i * 0.4,
      })),
    [],
  );

  const translated = MODULES.map((m) => ({
    module: m,
    desc: t(`labs.cognition.${m.id}_desc`, m.desc),
  }));

  return (
    <AnimatedPage>
      <div className="relative flex min-h-screen flex-col items-center overflow-hidden bg-[#020202] px-6 py-20 text-[#F4F1E8]">
        {/* Poussière d'étoiles */}
        <div className="pointer-events-none fixed inset-0 z-0">
          {particleConfig.map((p, i) => (
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
        {/* Lueur du noyau */}
        <div className="pointer-events-none fixed inset-0 z-0 opacity-10">
          <div className="absolute left-1/3 top-1/3 h-[500px] w-[500px] rounded-full bg-[#5D7FD3]/30 blur-[150px]" />
          <div className="absolute bottom-1/4 right-1/4 h-[400px] w-[400px] rounded-full bg-[#E8442B]/20 blur-[150px]" />
        </div>

        <header className="z-10 mb-10 text-center">
          <h1 className="manga-font text-6xl font-black uppercase italic tracking-tighter text-white md:text-7xl">
            COGNITION{' '}
            <span className="text-[#5D7FD3] drop-shadow-[0_0_15px_rgba(93,127,211,0.5)]">CORE</span>
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-white/40">
            {t(
              'labs.cognition.hero_title',
              "Fusion de l'identité numérique, de la mémoire artificielle et de la simulation de futurs possibles.",
            )}
          </p>
        </header>

        {/* La constellation : trois synapses reliées (desktop) */}
        <div className="relative z-10 hidden h-[560px] w-full max-w-5xl md:block">
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden
          >
            <line
              x1={MODULES[0].x + 11}
              y1={MODULES[0].y + 11}
              x2={MODULES[1].x + 11}
              y2={MODULES[1].y + 11}
              stroke="#F4F1E8"
              strokeOpacity="0.12"
              strokeWidth="0.2"
              strokeDasharray="1.5 1.5"
            />
            <line
              x1={MODULES[1].x + 11}
              y1={MODULES[1].y + 11}
              x2={MODULES[2].x + 11}
              y2={MODULES[2].y + 11}
              stroke="#F4F1E8"
              strokeOpacity="0.12"
              strokeWidth="0.2"
              strokeDasharray="1.5 1.5"
            />
            <line
              x1={MODULES[2].x + 11}
              y1={MODULES[2].y + 11}
              x2={MODULES[0].x + 11}
              y2={MODULES[0].y + 11}
              stroke="#F4F1E8"
              strokeOpacity="0.12"
              strokeWidth="0.2"
              strokeDasharray="1.5 1.5"
            />
          </svg>
          {translated.map(({ module, desc }) => (
            <SynapseNode
              key={module.id}
              module={module}
              desc={desc}
              className="absolute"
              style={{ left: `${module.x}%`, top: `${module.y}%` }}
            />
          ))}
        </div>

        {/* Mobile : synapses empilées */}
        <div className="z-10 flex flex-col items-center gap-14 md:hidden">
          {translated.map(({ module, desc }) => (
            <SynapseNode key={module.id} module={module} desc={desc} />
          ))}
        </div>

        <footer className="z-10 mt-auto pt-16 text-center">
          <p className="mx-auto max-w-2xl text-[11px] leading-relaxed text-white/25">
            {t(
              'labs.cognition.guide_footer_1',
              "Le Cognition Hub unifie les vecteurs d'identité et de décision.",
            )}{' '}
            {t(
              'labs.cognition.guide_footer_2',
              "Les données traitées ici servent à affiner les modèles de recommandation neuro-symboliques sans compromettre l'étanchéité de la vie privée numérique.",
            )}
          </p>
        </footer>
      </div>
    </AnimatedPage>
  );
};

export default CognitionHubPage;
