import React, { useMemo, useState } from 'react';
import { Compass, Layers, MapPin, Radar } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { motion, useReducedMotion } from 'framer-motion';
import { apiClient } from '../../utils/apiClient';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import {
  LANDSCAPE,
  PORTRAIT,
  isGenerating,
  surveyMap,
  useNarrow,
  type LoreCommunity,
  type WorldMapResponse,
} from './loreCartography';
import { Graticule, Plate } from './components/MapPlate';

/** Label court pour la planche : on retire le préfixe « Communauté » (redondant,
 *  chaque territoire en est une) et on tronque les noms longs — le nom complet
 *  reste dans le dossier et dans l'aria-label. Évite le télescopage des labels. */
const mapLabel = (name: string): string => {
  const short = name.replace(/^Communaut[ée]s?\s+/i, '').trim();
  return short.length > 22 ? `${short.slice(0, 21).trimEnd()}…` : short;
};

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
      <div className="min-h-screen bg-[#0B0C10]">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <Plate className="h-[520px] animate-pulse">
            <svg viewBox={`0 0 ${VIEW.w} ${VIEW.h}`} className="h-full w-full">
              <Graticule view={VIEW} />
            </svg>
          </Plate>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-[#0B0C10]">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <Plate className="p-12 text-center">
            <h2 className="font-manga text-3xl font-black uppercase italic text-[#E8442B]">
              Carte indisponible
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-[#8F94A5]">
              Le service de cartographie ne répond pas pour le moment. Réessayez dans un instant.
            </p>
          </Plate>
        </div>
      </div>
    );
  }

  return (
    <AnimatedPage>
      <div className="min-h-screen bg-[#0B0C10] bg-manga-overlay text-[#F4F1E8]">
        <div className="mx-auto max-w-7xl px-6 py-12">
          {/* En-tête de page, en clair, avant la planche. */}
          <header className="mb-8">
            <div className="mb-3 flex items-center gap-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                図
              </span>
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                Atlas du lore
              </span>
            </div>
            <h1 className="font-manga text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-6xl">
              Lore World <span className="text-[#E8442B]">Map</span>
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#8F94A5]">
              Une carte des univers d&apos;anime : les œuvres qui se ressemblent sont regroupées en
              territoires. Cliquez sur l&apos;un d&apos;eux pour découvrir ce qu&apos;il contient.
            </p>
            <span className="mt-6 block h-px bg-[#F4F1E8]/10" aria-hidden />
          </header>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
            {/* ── La planche : la carte EST le héros ── */}
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
                          y={t.cy + t.r + 16}
                          textAnchor="middle"
                          className="pointer-events-none select-none font-mono uppercase"
                          fontSize={10.5}
                          letterSpacing={1.5}
                          fill="#f1f2f6"
                          fillOpacity={isActive ? 0.95 : 0.45}
                        >
                          {mapLabel(t.community.name)}
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

                  {/* Échelle — un instrument, pas une décoration : elle dit l'encodage. */}
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
                      Taille = nombre d&apos;œuvres
                    </text>
                  </g>
                </svg>

                {/* Cartouche discret sur la planche (le titre principal est au-dessus). */}
                <div className="pointer-events-none absolute left-6 top-6 flex items-center gap-2 lg:left-8 lg:top-8">
                  <span className="font-mono text-[9px] uppercase tracking-[0.35em] text-[#FDB913]/80">
                    {communities.length} territoires · {entityCount} œuvres
                  </span>
                </div>

                {generating && (
                  <div className="pointer-events-none absolute right-8 top-8 flex items-center gap-2 rounded-full border border-[#FDB913]/30 bg-[#FDB913]/10 px-4 py-2">
                    <Radar className="h-3.5 w-3.5 animate-spin text-[#FDB913] [animation-duration:3s]" />
                    <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-[#FDB913]">
                      Relevé en cours
                    </span>
                  </div>
                )}
              </Plate>

              {/* Relevés : le tableau de bord de la planche. */}
              <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
                {[
                  { icon: Layers, label: 'Territoires', value: communities.length },
                  { icon: MapPin, label: 'Œuvres', value: entityCount },
                  { icon: Compass, label: 'Méthode', value: 'Leiden' },
                ].map(({ icon: Icon, label, value }) => (
                  <div
                    key={label}
                    className="flex items-center gap-3 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] px-4 py-3"
                  >
                    <Icon className="h-4 w-4 shrink-0 text-[#FDB913]/70" />
                    <div className="min-w-0">
                      <p className="text-[9px] font-black uppercase tracking-[0.2em] text-[#8F94A5]">
                        {label}
                      </p>
                      <p className="font-manga truncate text-lg font-black uppercase italic text-[#F4F1E8]">
                        {value}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* ── Dossier : ce que contient le territoire sélectionné ── */}
            <div className="lg:col-span-4">
              <div className="sticky top-24 rounded-[2rem] border border-[#F4F1E8]/10 bg-[#0F1016] p-8">
                {selected ? (
                  <motion.div
                    key={String(selected.community.id)}
                    initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35 }}
                  >
                    <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#FDB913]">
                      Territoire
                    </p>
                    <h2 className="font-manga mt-2 text-2xl font-black uppercase italic leading-tight text-[#F4F1E8]">
                      {selected.community.name}
                    </h2>

                    <p className="mt-5 text-sm leading-relaxed text-[#8F94A5]">
                      {selected.community.summary}
                    </p>

                    <div className="mt-8">
                      <p className="text-[10px] font-black uppercase tracking-[0.25em] text-[#8F94A5]">
                        Œuvres de ce territoire ({selected.community.entities?.length ?? 0})
                      </p>
                      <ul className="mt-3 flex flex-wrap gap-2">
                        {(selected.community.entities ?? []).slice(0, 12).map((entity) => (
                          <li
                            key={entity}
                            className="rounded-full border border-[#FDB913]/20 bg-[#FDB913]/[0.06] px-3 py-1 text-[11px] font-bold text-[#FDB913]/90"
                          >
                            {entity}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <p className="mt-8 border-t border-[#F4F1E8]/10 pt-5 text-xs leading-relaxed text-[#8F94A5]/70">
                      Cliquez un autre territoire sur la carte pour ouvrir son dossier.
                    </p>
                  </motion.div>
                ) : (
                  <div>
                    <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#FDB913]">
                      {generating ? 'Relevé en cours' : 'Carte vierge'}
                    </p>
                    <h2 className="font-manga mt-2 text-2xl font-black uppercase italic leading-tight text-[#F4F1E8]">
                      {generating ? 'La carte se prépare' : 'Aucun territoire relevé'}
                    </h2>
                    <p className="mt-5 text-sm leading-relaxed text-[#8F94A5]">
                      {generating
                        ? "Les territoires s'afficheront ici dès que la carte est prête. Cette page se met à jour toute seule."
                        : 'La carte est reconstruite chaque nuit : les œuvres sont regroupées et chaque territoire reçoit un résumé.'}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ── Deux repères en clair : lire la carte, et d'où elle vient ── */}
          <div className="mt-20 grid grid-cols-1 gap-6 md:grid-cols-2">
            <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8">
              <h3 className="font-manga mb-5 flex items-center gap-3 text-lg font-black uppercase italic text-[#F4F1E8]">
                <Compass className="h-5 w-5 text-[#FDB913]" aria-hidden="true" /> Comment lire la
                carte
              </h3>
              <div className="space-y-4 text-sm leading-relaxed text-[#8F94A5]">
                <p>
                  <span className="font-bold text-[#F4F1E8]">Les territoires.</span> Chaque masse
                  regroupe des œuvres qui se ressemblent. Plus un territoire contient d&apos;œuvres,
                  plus il est grand.
                </p>
                <p>
                  <span className="font-bold text-[#F4F1E8]">Les points.</span> Ce sont les œuvres
                  du territoire. On ne trace aucun trait entre elles : la carte montre les
                  regroupements, elle n&apos;invente pas de liens.
                </p>
                <p>
                  <span className="font-bold text-[#F4F1E8]">La lecture.</span> Cliquez un
                  territoire (ou tabulez jusqu&apos;à lui) pour ouvrir son dossier : un résumé et
                  ses œuvres clés.
                </p>
              </div>
            </section>

            <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8">
              <h3 className="font-manga mb-5 flex items-center gap-3 text-lg font-black uppercase italic text-[#F4F1E8]">
                <Radar className="h-5 w-5 text-[#FDB913]" aria-hidden="true" /> D&apos;où vient
                cette carte
              </h3>
              <div className="space-y-4 text-sm leading-relaxed text-[#8F94A5]">
                <p>
                  <span className="font-bold text-[#F4F1E8]">Le regroupement.</span> Les œuvres sont
                  rassemblées non par titre, mais par ce qu&apos;elles ont en commun : thèmes,
                  auteurs, studios, inspirations (méthode dite « Leiden »).
                </p>
                <p>
                  <span className="font-bold text-[#F4F1E8]">La fabrication.</span> La carte est
                  préparée à l&apos;avance, la nuit. Elle n&apos;est jamais calculée pendant votre
                  visite — résumer chaque territoire coûte un appel à l&apos;IA.
                </p>
                <p>
                  <span className="font-bold text-[#F4F1E8]">À quoi ça sert.</span> Ces
                  regroupements aident l&apos;IA à saisir le contexte d&apos;une saga entière avant
                  d&apos;affiner une recherche.
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default LoreWorldMapPage;
