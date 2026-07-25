import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { cognitionLabs, type LabEntry } from './labHubData';

/**
 * Enrichissement propre au noyau cognitif : chaque lab reçoit une encre de
 * synapse et un sous-titre court. Les autres champs (titre, desc, url, glyph)
 * viennent de `cognitionLabs` — source unique, donc le hub ne peut plus oublier
 * un lab. Un id inconnu retombe sur l'indigo cognitif + son badge.
 */
const META: Record<string, { hex: string; sub: string }> = {
  archetype: { hex: '#5D7FD3', sub: 'Votre profil de goûts' },
  memory: { hex: '#FDB913', sub: 'Votre mémoire IA' },
  simulator: { hex: '#E8442B', sub: 'Futurs alternatifs' },
  latent: { hex: '#8B5CF6', sub: 'Carte des œuvres' },
  debate: { hex: '#F43F5E', sub: "Duels d'IA" },
  'graph-map': { hex: '#34D399', sub: 'Carte des univers' },
  strategy: { hex: '#38BDF8', sub: 'Le meilleur coup' },
};

const AI_INDIGO = '#5D7FD3';

interface Synapse extends LabEntry {
  hex: string;
  sub: string;
  /** position dans la constellation (viewBox 0..100) */
  x: number;
  y: number;
  float: number;
}

/** Centre de la constellation (le noyau) et rayons de l'orbite, en %. */
const CORE = { x: 50, y: 47 };
const RX = 37;
const RY = 34;

/** Répartit les labs sur une ellipse autour du noyau (premier en haut). */
const SYNAPSES: Synapse[] = cognitionLabs.map((lab, i) => {
  const angle = (i / cognitionLabs.length) * Math.PI * 2 - Math.PI / 2;
  const meta = META[lab.id] ?? { hex: AI_INDIGO, sub: lab.badge };
  return {
    ...lab,
    hex: meta.hex,
    sub: meta.sub,
    x: CORE.x + RX * Math.cos(angle),
    y: CORE.y + RY * Math.sin(angle),
    float: 5 + ((i * 5) % 4) * 0.5,
  };
});

/** Une synapse : nœud lumineux flottant + cartouche, navigation directe.
 *  Le survol/focus remonte au parent (légende unique) au lieu d'afficher une
 *  description sous le nœud, qui chevaucherait les bulles voisines. En mobile
 *  (empilé), la description reste en ligne — il y a la place. */
const SynapseNode: React.FC<{
  node: Synapse;
  desc: string;
  className?: string;
  style?: React.CSSProperties;
  onActivate?: (n: Synapse) => void;
  onDeactivate?: () => void;
}> = ({ node, desc, className = '', style, onActivate, onDeactivate }) => (
  <div className={className} style={style}>
    <motion.div
      animate={{ y: [0, -12, 0] }}
      transition={{ repeat: Infinity, duration: node.float, ease: 'easeInOut' }}
    >
      <Link
        to={node.url}
        onMouseEnter={() => onActivate?.(node)}
        onMouseLeave={() => onDeactivate?.()}
        onFocus={() => onActivate?.(node)}
        onBlur={() => onDeactivate?.()}
        className="group flex w-48 flex-col items-center text-center no-underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-8 focus-visible:outline-[#FDB913]"
      >
        <span className="relative mb-4 flex h-24 w-24 items-center justify-center">
          <span
            aria-hidden
            className="absolute inset-0 rounded-full opacity-30 blur-[28px] transition-opacity duration-500 group-hover:opacity-70"
            style={{ backgroundColor: node.hex }}
          />
          <span
            className="relative flex h-full w-full items-center justify-center rounded-full border-2 bg-[#020202]/80 text-4xl font-bold leading-none transition-transform duration-500 group-hover:scale-110"
            style={{ borderColor: `${node.hex}66`, color: node.hex }}
            aria-hidden
          >
            {node.glyph}
          </span>
        </span>
        <p
          className="mb-1 text-[9px] font-black uppercase tracking-widest"
          style={{ color: node.hex }}
        >
          {node.sub}
        </p>
        <h2 className="font-manga text-xl font-black uppercase italic leading-none text-white">
          {node.title}
        </h2>
        {/* Description en ligne réservée au mobile empilé (md:hidden). */}
        <p className="mt-2 text-[10px] leading-relaxed text-white/45 md:hidden">{desc}</p>
      </Link>
    </motion.div>
  </div>
);

const CognitionHubPage: React.FC = () => {
  const { t } = useTranslation();
  const [active, setActive] = React.useState<Synapse | null>(null);

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

  const translated = SYNAPSES.map((node) => ({
    node,
    desc: t(`labs.cognition.${node.id}_desc`, node.desc),
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
              "Les sept synapses du noyau cognitif. Cliquez sur l'une d'elles pour l'ouvrir.",
            )}
          </p>
          {/* Légende unique (desktop) : la description du nœud survolé s'affiche
              ici, en haut et toujours visible, pour ne jamais chevaucher les
              bulles voisines. Hauteur réservée → pas de saut de mise en page. */}
          <div className="mx-auto mt-5 hidden h-10 max-w-xl items-center justify-center md:flex">
            {active && (
              <p className="text-sm leading-relaxed text-white/70 animate-in fade-in duration-200">
                <span
                  className="text-[11px] font-black uppercase tracking-widest"
                  style={{ color: active.hex }}
                >
                  {active.title}
                </span>{' '}
                — {t(`labs.cognition.${active.id}_desc`, active.desc)}
              </p>
            )}
          </div>
        </header>

        {/* La constellation : le noyau + les synapses en orbite (desktop) */}
        <div className="relative z-10 hidden h-[620px] w-full max-w-5xl md:block">
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden
          >
            {SYNAPSES.map((node) => (
              <line
                key={node.id}
                x1={CORE.x}
                y1={CORE.y}
                x2={node.x}
                y2={node.y}
                stroke={node.hex}
                strokeOpacity="0.22"
                strokeWidth="0.18"
                strokeDasharray="1.2 1.4"
              />
            ))}
          </svg>

          {/* Noyau central */}
          <div
            className="absolute -translate-x-1/2 -translate-y-1/2"
            style={{ left: `${CORE.x}%`, top: `${CORE.y}%` }}
          >
            <div className="relative flex h-28 w-28 items-center justify-center">
              <span
                aria-hidden
                className="absolute inset-0 animate-pulse rounded-full bg-[#5D7FD3]/40 blur-[40px]"
              />
              <span
                className="relative flex h-full w-full items-center justify-center rounded-full border border-[#5D7FD3]/40 bg-[#020202]/90 text-5xl font-bold leading-none text-[#5D7FD3]"
                aria-hidden
              >
                核
              </span>
            </div>
          </div>

          {translated.map(({ node, desc }) => (
            <SynapseNode
              key={node.id}
              node={node}
              desc={desc}
              className="absolute -translate-x-1/2 -translate-y-1/2"
              style={{ left: `${node.x}%`, top: `${node.y}%` }}
              onActivate={setActive}
              onDeactivate={() => setActive(null)}
            />
          ))}
        </div>

        {/* Mobile : synapses empilées */}
        <div className="z-10 flex flex-col items-center gap-12 md:hidden">
          {translated.map(({ node, desc }) => (
            <SynapseNode key={node.id} node={node} desc={desc} />
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
