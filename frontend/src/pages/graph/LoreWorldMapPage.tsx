import React, { useMemo, useState } from 'react';
import { Compass, Layers, MapPin, Radar, Search, Sparkles } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { motion, useReducedMotion } from 'framer-motion';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

interface LoreCommunity {
  id: string | number;
  name: string;
  summary: string;
  entities?: string[];
}

// The endpoint answers with EITHER the community list OR, while the map is being
// (re)built, a 202 `{status: "generating"}`. Both are 2xx, so apiClient hands them
// through as data — the page must discriminate. It used to assume an array and
// crashed the error boundary with "e?.map is not a function".
type WorldMapResponse = LoreCommunity[] | { status?: string };

const isGenerating = (data: WorldMapResponse | undefined): boolean =>
  !!data && !Array.isArray(data) && (data as { status?: string }).status === 'generating';

/* ── Cartography ──────────────────────────────────────────────────────────────
 * The map is drawn from the data alone: no coordinates are stored, so every
 * shape is derived deterministically from the community's id (same data ->
 * same map, every render). Only two things are encoded, and both are true:
 * AREA = number of entities, CONTAINMENT = membership. Nothing is drawn between
 * entities — we do not have those edges, and a map must not invent terrain.
 * ─────────────────────────────────────────────────────────────────────────── */

/** The plate is landscape on a desktop and portrait on a phone: the SVG scales to
 *  the container width, so a landscape plate on a 390px screen would shrink every
 *  coast — and every label — to an unreadable sliver. */
const LANDSCAPE = { w: 1000, h: 620 };
const PORTRAIT = { w: 520, h: 660 };

const NARROW_QUERY = '(max-width: 1023px)';

// matchMedia is absent under jsdom and during SSR — fall back to the desktop plate
// rather than throwing.
const mediaQuery = () =>
  typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia(NARROW_QUERY)
    : null;

const useNarrow = () => {
  const [narrow, setNarrow] = useState(() => mediaQuery()?.matches ?? false);
  React.useEffect(() => {
    const mq = mediaQuery();
    if (!mq) return undefined;
    const onChange = (e: MediaQueryListEvent) => setNarrow(e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);
  return narrow;
};

/** Deterministic PRNG (mulberry32) seeded from a string. */
const seededRandom = (seed: string) => {
  let h = 1779033703 ^ seed.length;
  for (let i = 0; i < seed.length; i += 1) {
    h = Math.imul(h ^ seed.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  let a = h >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

/** Organic coastline: jittered radial points closed into a smooth cubic path. */
const coastline = (cx: number, cy: number, r: number, rand: () => number) => {
  const points = 11;
  const pts = Array.from({ length: points }, (_, i) => {
    const angle = (i / points) * Math.PI * 2;
    const radius = r * (0.78 + rand() * 0.42);
    return [cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius * 0.82];
  });

  // Catmull-Rom -> bezier, wrapped, so the coast closes without a seam.
  const at = (i: number) => pts[(i + pts.length) % pts.length];
  let d = `M ${at(0)[0].toFixed(1)} ${at(0)[1].toFixed(1)}`;
  for (let i = 0; i < pts.length; i += 1) {
    const [x0, y0] = at(i - 1);
    const [x1, y1] = at(i);
    const [x2, y2] = at(i + 1);
    const [x3, y3] = at(i + 2);
    const c1 = [x1 + (x2 - x0) / 6, y1 + (y2 - y0) / 6];
    const c2 = [x2 - (x3 - x1) / 6, y2 - (y3 - y1) / 6];
    d += ` C ${c1[0].toFixed(1)} ${c1[1].toFixed(1)}, ${c2[0].toFixed(1)} ${c2[1].toFixed(1)}, ${x2.toFixed(1)} ${y2.toFixed(1)}`;
  }
  return `${d} Z`;
};

interface PlateSize {
  w: number;
  h: number;
}

interface Territory {
  community: LoreCommunity;
  cx: number;
  cy: number;
  r: number;
  path: string;
  landmarks: { x: number; y: number; label: string }[];
}

/** Lays the territories out: a golden-angle spiral seeds the composition, then a
 *  deterministic relaxation pushes overlapping landmasses apart. Territories must
 *  never touch — on a map, a shared coastline reads as a shared border, and the
 *  data says nothing about relations BETWEEN communities. */
const surveyMap = (communities: LoreCommunity[], VIEW: PlateSize): Territory[] => {
  const GOLDEN = Math.PI * (3 - Math.sqrt(5));
  const count = communities.length;
  const spread = Math.min(VIEW.w, VIEW.h) * 0.34;
  const MARGIN = 26; // clear water + room for the label under each coast

  const nodes = communities.map((community, i) => {
    const entities = community.entities ?? [];
    // Area encodes the entity count -> the radius scales with its square root.
    const r = 40 + Math.sqrt(entities.length) * 20;
    const step = count === 1 ? 0 : Math.sqrt(i / Math.max(count - 1, 1));
    const angle = i * GOLDEN;
    return {
      community,
      r,
      x: VIEW.w / 2 + Math.cos(angle) * spread * step * 1.5,
      y: VIEW.h / 2 + Math.sin(angle) * spread * step,
    };
  });

  // The title cartouche is printed on the plate: treat it as an immovable island
  // so no coastline is ever drawn under the title.
  const cartouche = { x: VIEW.w * 0.13, y: VIEW.h * 0.1, r: VIEW.w < 700 ? 145 : 165 };

  for (let pass = 0; pass < 220; pass += 1) {
    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        const a = nodes[i];
        const b = nodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.hypot(dx, dy) || 0.01;
        const min = a.r + b.r + MARGIN;
        if (dist < min) {
          const push = (min - dist) / 2;
          const ux = dx / dist;
          const uy = dy / dist;
          a.x -= ux * push;
          a.y -= uy * push;
          b.x += ux * push;
          b.y += uy * push;
        }
      }
    }

    nodes.forEach((n) => {
      // Push out of the cartouche (it never moves).
      const dx = n.x - cartouche.x;
      const dy = n.y - cartouche.y;
      const dist = Math.hypot(dx, dy) || 0.01;
      const min = n.r + cartouche.r;
      if (dist < min) {
        n.x += (dx / dist) * (min - dist);
        n.y += (dy / dist) * (min - dist);
      }
      // Keep every coast (and its label) inside the plate.
      n.x = Math.min(VIEW.w - n.r - 24, Math.max(n.r + 24, n.x));
      n.y = Math.min(VIEW.h - n.r - 44, Math.max(n.r + 30, n.y));
    });
  }

  return nodes.map(({ community, r, x: cx, y: cy }) => {
    const rand = seededRandom(String(community.id) + community.name);
    const entities = community.entities ?? [];

    const landmarks = entities.slice(0, 7).map((label) => {
      const a = rand() * Math.PI * 2;
      const d = Math.sqrt(rand()) * r * 0.5;
      return { x: cx + Math.cos(a) * d, y: cy + Math.sin(a) * d * 0.8, label };
    });

    return { community, cx, cy, r, path: coastline(cx, cy, r, rand), landmarks };
  });
};

/* ── Plate ─────────────────────────────────────────────────────────────────── */

const Graticule: React.FC<{ view: PlateSize }> = ({ view: VIEW }) => (
  <g className="text-white/[0.05]">
    {Array.from({ length: 11 }, (_, i) => (
      <line
        key={`v${i}`}
        x1={(i * VIEW.w) / 10}
        y1={0}
        x2={(i * VIEW.w) / 10}
        y2={VIEW.h}
        stroke="currentColor"
        strokeWidth={1}
      />
    ))}
    {Array.from({ length: 7 }, (_, i) => (
      <line
        key={`h${i}`}
        x1={0}
        y1={(i * VIEW.h) / 6}
        x2={VIEW.w}
        y2={(i * VIEW.h) / 6}
        stroke="currentColor"
        strokeWidth={1}
      />
    ))}
  </g>
);

const Plate: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div
    className={`relative overflow-hidden rounded-[2rem] border border-anime-accent/15 bg-[#0a0a12] ${className}`}
  >
    <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-anime-accent/[0.07] blur-[90px]" />
    <div className="pointer-events-none absolute -bottom-32 -right-16 h-80 w-80 rounded-full bg-anime-accent/[0.05] blur-[110px]" />
    {children}
  </div>
);

/* ── Page ──────────────────────────────────────────────────────────────────── */

const LoreWorldMapPage: React.FC = () => {
  const reduceMotion = useReducedMotion();
  const narrow = useNarrow();
  const VIEW = narrow ? PORTRAIT : LANDSCAPE;
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery<WorldMapResponse>({
    queryKey: ['graph-world-map'],
    queryFn: () => apiClient('/api/v1/graph/world-map/'),
    // While the backend reports "generating", poll until the map lands.
    refetchInterval: (query) => (isGenerating(query.state.data) ? 5000 : false),
  });

  // Anything that is not a list of communities renders as "nothing surveyed yet"
  // rather than throwing (a malformed payload must not take the page down).
  const communities: LoreCommunity[] = useMemo(() => (Array.isArray(data) ? data : []), [data]);
  const generating = isGenerating(data);

  const territories = useMemo(() => surveyMap(communities, VIEW), [communities, VIEW]);
  const entityCount = communities.reduce((n, c) => n + (c.entities?.length ?? 0), 0);

  const selected = territories.find((t) => String(t.community.id) === selectedId) ?? territories[0];

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-16">
        <Plate className="h-[520px] animate-pulse">
          <svg viewBox={`0 0 ${VIEW.w} ${VIEW.h}`} className="h-full w-full">
            <Graticule view={VIEW} />
          </svg>
        </Plate>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-7xl px-6 py-24">
        <Plate className="p-12 text-center">
          <h2 className="manga-font text-3xl text-red-500">Relevé impossible</h2>
          <p className="mt-4 font-mono text-xs uppercase tracking-[0.25em] text-white/40">
            Le service de cartographie ne répond pas. Réessayez dans un moment.
          </p>
        </Plate>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="mx-auto max-w-7xl px-6 py-12">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
          {/* ── The plate: the map IS the hero, the title is its cartouche ── */}
          <div className="lg:col-span-8">
            <Plate>
              <svg
                viewBox={`0 0 ${VIEW.w} ${VIEW.h}`}
                className="h-full w-full"
                role="img"
                aria-label={`Carte du lore : ${communities.length} territoires relevés`}
              >
                <defs>
                  <radialGradient id="land" cx="35%" cy="30%">
                    <stop offset="0%" stopColor="#fdb913" stopOpacity="0.30" />
                    <stop offset="100%" stopColor="#fdb913" stopOpacity="0.07" />
                  </radialGradient>
                  <radialGradient id="landActive" cx="35%" cy="30%">
                    <stop offset="0%" stopColor="#fdb913" stopOpacity="0.55" />
                    <stop offset="100%" stopColor="#fdb913" stopOpacity="0.18" />
                  </radialGradient>
                </defs>

                <Graticule view={VIEW} />

                {territories.map((t, i) => {
                  const id = String(t.community.id);
                  const isActive = selected && String(selected.community.id) === id;
                  const isDimmed = hoveredId !== null && hoveredId !== id;

                  return (
                    <motion.g
                      key={id}
                      role="button"
                      tabIndex={0}
                      aria-label={`${t.community.name} — ${t.community.entities?.length ?? 0} entités`}
                      aria-pressed={!!isActive}
                      className="cursor-pointer outline-none focus-visible:[&>path]:stroke-white"
                      onClick={() => setSelectedId(id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault();
                          setSelectedId(id);
                        }
                      }}
                      onMouseEnter={() => setHoveredId(id)}
                      onMouseLeave={() => setHoveredId(null)}
                      onFocus={() => setHoveredId(id)}
                      onBlur={() => setHoveredId(null)}
                      initial={reduceMotion ? false : { opacity: 0 }}
                      animate={{ opacity: isDimmed ? 0.28 : 1 }}
                      transition={{ delay: reduceMotion ? 0 : i * 0.12, duration: 0.5 }}
                    >
                      {/* Coastline: drawn in, like a survey being plotted. */}
                      <motion.path
                        d={t.path}
                        fill={isActive ? 'url(#landActive)' : 'url(#land)'}
                        stroke="#fdb913"
                        strokeWidth={isActive ? 2 : 1}
                        strokeOpacity={isActive ? 0.9 : 0.35}
                        initial={reduceMotion ? false : { pathLength: 0 }}
                        animate={{ pathLength: 1 }}
                        transition={{
                          delay: reduceMotion ? 0 : 0.2 + i * 0.12,
                          duration: reduceMotion ? 0 : 1.1,
                          ease: 'easeInOut',
                        }}
                      />

                      {/* Landmarks = the community's entities. Containment is the
                          only relation we actually know, so it is the only one drawn. */}
                      {t.landmarks.map((m) => (
                        <circle
                          key={m.label}
                          cx={m.x}
                          cy={m.y}
                          r={isActive ? 3 : 2}
                          fill="#fdb913"
                          fillOpacity={isActive ? 0.95 : 0.5}
                        />
                      ))}

                      <text
                        x={t.cx}
                        y={t.cy + t.r + 18}
                        textAnchor="middle"
                        className="pointer-events-none select-none font-mono uppercase"
                        fontSize={11}
                        letterSpacing={2}
                        fill="#f1f2f6"
                        fillOpacity={isActive ? 0.95 : 0.4}
                      >
                        {t.community.name}
                      </text>
                    </motion.g>
                  );
                })}

                {/* Unsurveyed plate: the empty state speaks the map's language. */}
                {territories.length === 0 && (
                  <text
                    x={VIEW.w / 2}
                    y={VIEW.h / 2}
                    textAnchor="middle"
                    className="font-mono uppercase"
                    fontSize={13}
                    letterSpacing={4}
                    fill="#fdb913"
                    fillOpacity={0.55}
                  >
                    {generating ? 'RELEVÉ EN COURS' : 'AUCUN TERRITOIRE RELEVÉ'}
                  </text>
                )}

                {/* Scale bar — an instrument, not decoration: it states the encoding. */}
                <g transform={`translate(32, ${VIEW.h - 34})`}>
                  <line
                    x1={0}
                    y1={0}
                    x2={60}
                    y2={0}
                    stroke="#fdb913"
                    strokeOpacity={0.5}
                    strokeWidth={2}
                  />
                  <text
                    x={70}
                    y={4}
                    className="font-mono uppercase"
                    fontSize={9}
                    letterSpacing={2}
                    fill="#f1f2f6"
                    fillOpacity={0.35}
                  >
                    Aire ∝ nombre d'entités
                  </text>
                </g>
              </svg>

              {/* Cartouche: on a desktop plate the title sits ON the map, as it would
                  on a real survey sheet. On a phone the map needs every pixel, so the
                  cartouche moves above it instead of covering the coasts. */}
              <div className="pointer-events-none absolute left-6 top-6 max-w-xs border-l-2 border-anime-accent/60 pl-4 lg:left-8 lg:top-8">
                <p className="font-mono text-[9px] uppercase tracking-[0.35em] text-anime-accent/80">
                  Division macro-sémantique
                </p>
                <h1 className="manga-font mt-1 text-2xl leading-none text-white lg:text-3xl">
                  Lore World Map
                </h1>
                <p className="mt-2 hidden font-mono text-[10px] uppercase leading-relaxed tracking-[0.15em] text-white/40 sm:block">
                  Relevé des communautés du graphe — partition Leiden
                </p>
              </div>

              {generating && (
                <div className="pointer-events-none absolute right-8 top-8 flex items-center gap-2 rounded-full border border-anime-accent/30 bg-anime-accent/10 px-4 py-2">
                  <Radar className="h-3.5 w-3.5 animate-spin text-anime-accent [animation-duration:3s]" />
                  <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-anime-accent">
                    Relevé en cours
                  </span>
                </div>
              )}
            </Plate>

            {/* Readings: the plate's instrument panel. Dark like the plate — the
                app chrome may be light, and a stat you cannot read is not a stat. */}
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              {[
                { icon: Layers, label: 'Territoires', value: communities.length },
                { icon: MapPin, label: 'Entités', value: entityCount },
                { icon: Compass, label: 'Partition', value: 'LEIDEN' },
              ].map(({ icon: Icon, label, value }) => (
                <div
                  key={label}
                  className="flex items-center gap-3 rounded-2xl border border-anime-accent/10 bg-[#12121f] px-4 py-3"
                >
                  <Icon className="h-4 w-4 shrink-0 text-anime-accent/70" />
                  <div className="min-w-0">
                    <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-white/40">
                      {label}
                    </p>
                    <p className="manga-font truncate text-lg text-white">{value}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Dossier: what the selected territory contains ── */}
          <div className="lg:col-span-4">
            <Card
              padding="lg"
              className="!bg-[#12121f] sticky top-24 rounded-[2rem] border-white/10"
            >
              {selected ? (
                <motion.div
                  key={String(selected.community.id)}
                  initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.35 }}
                >
                  <p className="font-mono text-[9px] uppercase tracking-[0.3em] text-anime-accent/80">
                    Territoire relevé
                  </p>
                  <h2 className="manga-font mt-2 text-2xl leading-tight text-white">
                    {selected.community.name}
                  </h2>

                  <p className="mt-5 text-sm leading-relaxed text-white/55">
                    {selected.community.summary}
                  </p>

                  <div className="mt-8">
                    <p className="font-mono text-[9px] uppercase tracking-[0.25em] text-white/35">
                      Points de repère ({selected.community.entities?.length ?? 0})
                    </p>
                    <ul className="mt-3 flex flex-wrap gap-2">
                      {(selected.community.entities ?? []).slice(0, 12).map((entity) => (
                        <li
                          key={entity}
                          className="rounded-full border border-anime-accent/20 bg-anime-accent/[0.06] px-3 py-1 font-mono text-[10px] uppercase tracking-wider text-anime-accent/90"
                        >
                          {entity}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <p className="mt-8 border-t border-white/5 pt-5 font-mono text-[10px] uppercase leading-relaxed tracking-wide text-white/30">
                    Sélectionnez un territoire sur la planche pour ouvrir son dossier.
                  </p>
                </motion.div>
              ) : (
                <div>
                  <p className="font-mono text-[9px] uppercase tracking-[0.3em] text-anime-accent/80">
                    {generating ? 'Relevé en cours' : 'Planche vierge'}
                  </p>
                  <h2 className="manga-font mt-2 text-2xl leading-tight text-white">
                    {generating ? 'Le graphe se partitionne' : 'Aucun territoire relevé'}
                  </h2>
                  <p className="mt-5 text-sm leading-relaxed text-white/55">
                    {generating
                      ? "Les territoires s'afficheront ici dès la fin du partitionnement. Cette page se met à jour toute seule."
                      : 'La carte est reconstruite par le job MLOps nocturne, qui repartitionne le graphe et résume chaque communauté.'}
                  </p>
                </div>
              )}
            </Card>
          </div>
        </div>

        {/* ── Guide & Protocole (convention des pages Lab) ── */}
        <div className="mt-24 grid grid-cols-1 gap-8 md:grid-cols-2">
          <Card
            padding="lg"
            className="group relative overflow-hidden !bg-[#12121f] border-anime-accent/20 shadow-[0_0_50px_rgba(253,185,19,0.06)]"
          >
            <div className="absolute -bottom-12 -right-12 opacity-5 transition-opacity group-hover:opacity-10">
              <Compass className="h-64 w-64 text-anime-accent" />
            </div>
            <h4 className="manga-font mb-4 flex items-center gap-3 text-xl text-white">
              <Sparkles className="h-5 w-5 text-anime-accent" /> Guide de la carte
            </h4>
            <div className="relative z-10 space-y-4">
              <p className="text-xs font-bold uppercase leading-relaxed tracking-wider text-white/60">
                <span className="text-anime-accent">Les territoires :</span> chaque masse est une
                communauté détectée dans le graphe. Son aire dépend du nombre d'entités qu'elle
                regroupe — une grande île est un thème dense.
              </p>
              <p className="text-xs font-bold uppercase leading-relaxed tracking-wider text-white/60">
                <span className="text-anime-accent">Les points de repère :</span> les entités
                membres du territoire. Aucun trait n'est tracé entre elles : le graphe ne nous donne
                pas ces liens, et la carte n'invente rien.
              </p>
              <p className="text-xs font-bold uppercase leading-relaxed tracking-wider text-white/60">
                <span className="text-anime-accent">La lecture :</span> cliquez un territoire (ou
                tabulez jusqu'à lui) pour ouvrir son dossier : résumé macro-conceptuel et entités
                clés.
              </p>
            </div>
          </Card>

          <Card
            padding="lg"
            className="group relative overflow-hidden !bg-[#12121f] border-white/10"
          >
            <div className="absolute -bottom-12 -right-12 opacity-5 transition-opacity group-hover:opacity-10">
              <Search className="h-64 w-64 text-white" />
            </div>
            <h4 className="manga-font mb-4 flex items-center gap-3 text-xl text-white">
              <Radar className="h-5 w-5 text-anime-accent" /> Protocole
            </h4>
            <div className="relative z-10 space-y-4">
              <p className="text-xs font-bold uppercase leading-relaxed tracking-wider text-white/60">
                <span className="text-anime-accent">Le partitionnement :</span> l'algorithme de
                Leiden regroupe les œuvres non par titre, mais par densité de relations (thèmes,
                auteurs, studios, inspirations).
              </p>
              <p className="text-xs font-bold uppercase leading-relaxed tracking-wider text-white/60">
                <span className="text-anime-accent">Le relevé :</span> la carte est pré-calculée par
                le job MLOps nocturne. Elle n'est jamais générée pendant votre visite — le résumé de
                chaque communauté coûte un appel au modèle.
              </p>
              <p className="text-xs font-bold uppercase leading-relaxed tracking-wider text-white/60">
                <span className="text-anime-accent">L'usage :</span> ces communautés servent à
                l'Expert Nexus, qui récupère le contexte macro d'une saga entière avant d'affiner sa
                recherche.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default LoreWorldMapPage;
