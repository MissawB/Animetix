import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
  Zap,
  Flame,
  Image as ImageIcon,
  Loader2,
  ChevronLeft,
  ChevronRight,
  ImageOff,
} from 'lucide-react';
import { CyberTerminalPanel } from '../../components/forge/CyberTerminalPanel';
import { useForge, FUSION_COST } from '../../hooks/useForge';
import { ForgeItemSelector } from '../../components/forge/ForgeItemSelector';
import { ForgeReactorPanel } from '../../components/forge/ForgeReactorPanel';
import { ForgeResultDisplay } from '../../components/forge/ForgeResultDisplay';

/** Titre de section d'atelier : barre braise + Montserrat. */
const PanelTitle: React.FC<{ icon: React.ReactNode; children: React.ReactNode }> = ({
  icon,
  children,
}) => (
  <h3 className="font-manga mb-6 flex items-center gap-3 text-lg font-black uppercase italic tracking-wide text-[#F4F1E8]">
    <span className="h-4 w-1 flex-none bg-[#FDB913]" aria-hidden />
    {icon}
    {children}
    <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
  </h3>
);

const ForgePage: React.FC = () => {
  const { t } = useTranslation();

  const {
    itemA,
    setItemA,
    itemB,
    setItemB,
    chaosLevel,
    setChaosLevel,
    balance,
    setBalance,
    artStyle,
    setArtStyle,
    styleDir,
    setStyleDir,
    isGenerating,
    fusionData,
    status,
    error,
    walletBalance,
    isAuthenticated,
    handleStartFusion,
    resetForge,
  } = useForge();

  const ART_STYLES = useMemo(
    () => [
      {
        id: 'Cyberpunk',
        name: t('games.forge.styles.cyberpunk_name', 'Cyberpunk'),
        desc: t('games.forge.styles.cyberpunk_desc', 'Néons et technologie futuriste'),
        image: '/static/img/forge/styles/cyberpunk.png',
      },
      {
        id: 'Ukiyo-e',
        name: t('games.forge.styles.ukiyoe_name', 'Ukiyo-e'),
        desc: t('games.forge.styles.ukiyoe_desc', 'Estampe traditionnelle japonaise'),
        image: '/static/img/forge/styles/ukiyo-e.png',
      },
      {
        id: 'Noir & Blanc',
        name: t('games.forge.styles.manga_noir_name', 'Manga Noir'),
        desc: t('games.forge.styles.manga_noir_desc', 'Contraste élevé, trames classiques'),
        image: '/static/img/forge/styles/manga-noir.png',
      },
      {
        id: 'Vaporwave',
        name: t('games.forge.styles.vaporwave_name', 'Vaporwave'),
        desc: t('games.forge.styles.vaporwave_desc', 'Esthétique rétro 80s, couleurs pastel'),
        image: '/static/img/forge/styles/vaporwave.png',
      },
      {
        id: 'Steampunk',
        name: t('games.forge.styles.steampunk_name', 'Steampunk'),
        desc: t('games.forge.styles.steampunk_desc', 'Cuivre, vapeur et engrenages'),
        image: '/static/img/forge/styles/steampunk.png',
      },
      {
        id: 'Aquarelle',
        name: t('games.forge.styles.aquarelle_name', 'Aquarelle'),
        desc: t('games.forge.styles.aquarelle_desc', 'Douceur et transparences fluides'),
        image: '/static/img/forge/styles/aquarelle.png',
      },
      {
        id: 'Pixel Art',
        name: t('games.forge.styles.pixel_art_name', 'Pixel Art'),
        desc: t('games.forge.styles.pixel_art_desc', 'Rétro 8-bit, pixels et arcade'),
        image: '/static/img/forge/styles/pixel-art.png',
      },
      {
        id: 'Gothique',
        name: t('games.forge.styles.gothique_name', 'Gothique'),
        desc: t('games.forge.styles.gothique_desc', 'Victorien sombre et dramatique'),
        image: '/static/img/forge/styles/gothique.png',
      },
      {
        id: 'Mecha',
        name: t('games.forge.styles.mecha_name', 'Mecha'),
        desc: t('games.forge.styles.mecha_desc', 'Robots géants et science-fiction'),
        image: '/static/img/forge/styles/mecha.png',
      },
      {
        id: '',
        name: t('games.forge.styles.brut_name', 'Brut'),
        desc: t(
          'games.forge.styles.brut_desc',
          'Aucune esthétique imposée — fusion la plus fidèle',
        ),
        image: '',
      },
    ],
    [t],
  );

  const cycleStyle = (dir: number) => {
    setStyleDir(dir);
    setArtStyle((prev) => {
      const i = ART_STYLES.findIndex((s) => s.id === prev);
      return ART_STYLES[(i + dir + ART_STYLES.length) % ART_STYLES.length].id;
    });
  };

  const goToStyle = (id: string) => {
    const from = ART_STYLES.findIndex((s) => s.id === artStyle);
    const to = ART_STYLES.findIndex((s) => s.id === id);
    setStyleDir(to >= from ? 1 : -1);
    setArtStyle(id);
  };

  // --- LA COULÉE (génération en cours) ---
  if (isGenerating || (fusionData && !status?.completed)) {
    return (
      <div className="flex min-h-[80vh] items-center justify-center bg-[#0B0C10] px-6 text-[#F4F1E8]">
        <div className="relative w-full max-w-3xl">
          <div className="absolute left-1/2 top-1/2 h-96 w-96 -translate-x-1/2 -translate-y-1/2 animate-pulse rounded-full bg-[#E8442B]/15 blur-[120px]" />

          <div className="relative z-10 overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-12 text-center">
            <div className="absolute left-0 top-0 h-1.5 w-full bg-[#F4F1E8]/5">
              <div
                className="h-full animate-[loading_2s_ease-in-out_infinite] bg-gradient-to-r from-[#FDB913] to-[#E8442B]"
                style={{ width: '30%' }}
              />
            </div>

            <span
              className="explore-stamp mx-auto mb-8 inline-block -rotate-2 text-2xl"
              aria-hidden
            >
              鍛
            </span>

            <h2 className="font-manga mb-2 text-4xl font-black uppercase italic tracking-tight md:text-5xl">
              {t('games.forge.loading_title', 'ALCHIMIE EN COURS')}
            </h2>
            <p className="mb-12 text-sm text-[#8F94A5]">
              {t('games.forge.tagline', 'Fusionnez deux univers en une œuvre inédite')}
            </p>

            <div className="mb-12 flex items-center justify-center gap-10">
              <div className="text-center">
                {itemA?.image_url ? (
                  <img
                    src={itemA.image_url}
                    className="aspect-[7/10] w-28 rounded-[4px] object-cover brightness-50 grayscale ring-1 ring-[#FDB913]/40"
                    alt=""
                    loading="lazy"
                    decoding="async"
                  />
                ) : (
                  <div className="flex aspect-[7/10] w-28 items-center justify-center rounded-[4px] bg-[#0B0C10] ring-1 ring-[#F4F1E8]/10">
                    <ImageIcon className="h-8 w-8 text-[#F4F1E8]/20" />
                  </div>
                )}
                <p className="mt-3 max-w-[112px] truncate text-[10px] font-black uppercase text-[#8F94A5]">
                  {itemA?.title || itemA?.name}
                </p>
              </div>

              <div className="flex flex-col items-center">
                <Loader2 className="mb-2 h-9 w-9 animate-spin text-[#FDB913]" />
                <div className="h-0.5 w-14 bg-gradient-to-r from-transparent via-[#E8442B] to-transparent" />
              </div>

              <div className="text-center">
                {itemB?.image_url ? (
                  <img
                    src={itemB.image_url}
                    className="aspect-[7/10] w-28 rounded-[4px] object-cover brightness-50 grayscale ring-1 ring-[#FDB913]/40"
                    alt=""
                    loading="lazy"
                    decoding="async"
                  />
                ) : (
                  <div className="flex aspect-[7/10] w-28 items-center justify-center rounded-[4px] bg-[#0B0C10] ring-1 ring-[#F4F1E8]/10">
                    <ImageIcon className="h-8 w-8 text-[#F4F1E8]/20" />
                  </div>
                )}
                <p className="mt-3 max-w-[112px] truncate text-[10px] font-black uppercase text-[#8F94A5]">
                  {itemB?.title || itemB?.name}
                </p>
              </div>
            </div>

            <div className="mx-auto max-w-md rounded-xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-6 text-left">
              <p className="h-6 overflow-hidden font-mono text-xs text-[#8F94A5]">
                {`> SEQ: INITIALIZING MULTIVERSAL BRIDGE...`}
              </p>
              <p className="mt-1 font-mono text-xs text-[#FDB913]">
                {`> STATUS: ${status?.status || 'COLLECTING CONCEPTUAL DATA'}`}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // --- L'ŒUVRE (résultat) ---
  if (status?.completed) {
    return (
      <ForgeResultDisplay
        status={status}
        fusionData={fusionData}
        itemA={itemA}
        itemB={itemB}
        artStyle={artStyle}
        chaosLevel={chaosLevel}
        resetForge={resetForge}
      />
    );
  }

  // --- L'ATELIER (configuration) ---
  return (
    <div className="min-h-screen bg-[#0B0C10] text-[#F4F1E8]">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
        <header className="relative mb-16">
          <div
            className="explore-halftone pointer-events-none absolute -inset-x-6 -top-10 h-44"
            aria-hidden
          />
          <div className="relative flex items-center gap-3">
            <span className="explore-stamp -rotate-2" aria-hidden>
              鍛
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              {t('games.forge.tagline', 'Fusionnez deux univers en une œuvre inédite')}
            </span>
          </div>
          <h1 className="font-manga relative mt-4 text-6xl font-black uppercase italic leading-none tracking-tighter md:text-8xl">
            {t('navbar.forge', 'LA FORGE')
              .split(' ')
              .map((word, i, arr) =>
                i === arr.length - 1 ? (
                  <span
                    key={word}
                    className="bg-gradient-to-br from-[#FDB913] to-[#E8442B] bg-clip-text text-transparent"
                  >
                    {word}
                  </span>
                ) : (
                  <span key={word}>{word} </span>
                ),
              )}
          </h1>
          <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
        </header>

        <div className="mb-16 grid grid-cols-1 gap-8 lg:grid-cols-12">
          <div className="space-y-8 lg:col-span-7">
            <CyberTerminalPanel>
              <PanelTitle icon={<Zap className="h-5 w-5 text-[#FDB913]" aria-hidden="true" />}>
                {t('games.forge.universe_selector', "Sélecteur d'Univers")}
              </PanelTitle>
              <ForgeItemSelector
                itemA={itemA}
                setItemA={setItemA}
                itemB={itemB}
                setItemB={setItemB}
              />
            </CyberTerminalPanel>

            <CyberTerminalPanel>
              <PanelTitle
                icon={<ImageIcon className="h-5 w-5 text-[#FDB913]" aria-hidden="true" />}
              >
                {t('games.forge.visual_aesthetic', 'Esthétique Visuelle')}
              </PanelTitle>
              {(() => {
                const len = ART_STYLES.length;
                const idx = Math.max(
                  0,
                  ART_STYLES.findIndex((s) => s.id === artStyle),
                );
                const current = ART_STYLES[idx];
                const prev = ART_STYLES[(idx - 1 + len) % len];
                const next = ART_STYLES[(idx + 1) % len];
                const visual = (s: (typeof ART_STYLES)[number]) =>
                  s.image ? (
                    <img
                      src={s.image}
                      alt={s.name}
                      loading="lazy"
                      decoding="async"
                      className="absolute inset-0 h-full w-full object-cover"
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-[#0F1016] to-[#0B0C10]">
                      <ImageOff className="h-12 w-12 text-[#F4F1E8]/25" />
                    </div>
                  );
                const slide = {
                  enter: (d: number) => ({ x: d >= 0 ? 220 : -220, opacity: 0 }),
                  center: { x: 0, opacity: 1 },
                  exit: (d: number) => ({ x: d >= 0 ? -220 : 220, opacity: 0 }),
                };
                return (
                  <div className="flex flex-col items-center">
                    <div className="relative flex h-[300px] w-full select-none items-center justify-center overflow-hidden">
                      {/* Voisin : précédent (en retrait, flouté) */}
                      <button
                        onClick={() => cycleStyle(-1)}
                        aria-label={t('games.forge.aria_prev_style_named', {
                          defaultValue: 'Style précédent : {{name}}',
                          name: prev.name,
                        })}
                        style={{
                          transform: 'translate(-50%, -50%) translateX(-148px) scale(0.78)',
                        }}
                        className="absolute left-1/2 top-1/2 z-0 aspect-[3/4] w-[200px] overflow-hidden rounded-xl opacity-40 blur-[3px] transition-all duration-300 hover:opacity-70 hover:blur-[1px]"
                      >
                        {visual(prev)}
                        <div className="absolute inset-0 bg-black/40" />
                      </button>

                      {/* Voisin : suivant (en retrait, flouté) */}
                      <button
                        onClick={() => cycleStyle(1)}
                        aria-label={t('games.forge.aria_next_style_named', {
                          defaultValue: 'Style suivant : {{name}}',
                          name: next.name,
                        })}
                        style={{
                          transform: 'translate(-50%, -50%) translateX(148px) scale(0.78)',
                        }}
                        className="absolute left-1/2 top-1/2 z-0 aspect-[3/4] w-[200px] overflow-hidden rounded-xl opacity-40 blur-[3px] transition-all duration-300 hover:opacity-70 hover:blur-[1px]"
                      >
                        {visual(next)}
                        <div className="absolute inset-0 bg-black/40" />
                      </button>

                      {/* Style courant — glissable */}
                      <AnimatePresence initial={false} custom={styleDir} mode="popLayout">
                        <motion.div
                          key={current.id || 'brut'}
                          custom={styleDir}
                          variants={slide}
                          initial="enter"
                          animate="center"
                          exit="exit"
                          transition={{
                            x: { type: 'spring', stiffness: 320, damping: 32 },
                            opacity: { duration: 0.18 },
                          }}
                          drag="x"
                          dragConstraints={{ left: 0, right: 0 }}
                          dragElastic={0.7}
                          onDragEnd={(_e, info) => {
                            if (info.offset.x < -60) cycleStyle(1);
                            else if (info.offset.x > 60) cycleStyle(-1);
                          }}
                          className="relative z-10 aspect-[3/4] w-[210px] cursor-grab touch-pan-y overflow-hidden rounded-xl border-2 border-[#FDB913] shadow-2xl ring-4 ring-[#FDB913]/15 active:cursor-grabbing"
                        >
                          {visual(current)}
                          <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/95 via-black/30 to-transparent" />
                          <span className="pointer-events-none absolute left-3 top-3 rounded-full bg-[#FDB913] px-2.5 py-1 text-[10px] font-black uppercase tracking-tighter text-black shadow">
                            {idx + 1}/{len}
                          </span>
                          <div className="pointer-events-none absolute inset-x-0 bottom-0 p-4 text-left">
                            <div className="mb-1 text-xl font-black uppercase italic leading-none text-white drop-shadow-md">
                              {current.name}
                            </div>
                            <div className="text-[11px] font-bold leading-tight text-white/70">
                              {current.desc}
                            </div>
                          </div>
                        </motion.div>
                      </AnimatePresence>

                      {/* Flèches */}
                      <button
                        onClick={() => cycleStyle(-1)}
                        aria-label={t('games.forge.aria_prev_style', 'Style précédent')}
                        className="absolute left-1 top-1/2 z-30 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/60 text-white shadow-lg backdrop-blur transition-all hover:bg-[#FDB913] hover:text-black active:scale-90"
                      >
                        <ChevronLeft className="h-6 w-6" />
                      </button>
                      <button
                        onClick={() => cycleStyle(1)}
                        aria-label={t('games.forge.aria_next_style', 'Style suivant')}
                        className="absolute right-1 top-1/2 z-30 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/60 text-white shadow-lg backdrop-blur transition-all hover:bg-[#FDB913] hover:text-black active:scale-90"
                      >
                        <ChevronRight className="h-6 w-6" />
                      </button>
                    </div>

                    <div className="mt-5 flex flex-wrap justify-center gap-2">
                      {ART_STYLES.map((s) => (
                        <button
                          key={s.id || 'brut'}
                          onClick={() => goToStyle(s.id)}
                          aria-label={t('games.forge.aria_choose_style', {
                            defaultValue: 'Choisir {{name}}',
                            name: s.name,
                          })}
                          aria-pressed={s.id === artStyle}
                          className={`h-2 rounded-full transition-all ${
                            s.id === artStyle
                              ? 'w-6 bg-[#FDB913]'
                              : 'w-2 bg-[#F4F1E8]/20 hover:bg-[#FDB913]/50'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                );
              })()}
            </CyberTerminalPanel>
          </div>

          <div className="space-y-8 lg:col-span-5">
            <CyberTerminalPanel className="sticky top-24">
              <PanelTitle icon={<Flame className="h-5 w-5 text-[#E8442B]" aria-hidden="true" />}>
                {t('games.forge.reactor_settings', 'Paramètres du Réacteur')}
              </PanelTitle>
              <ForgeReactorPanel
                itemA={itemA}
                itemB={itemB}
                chaosLevel={chaosLevel}
                setChaosLevel={setChaosLevel}
                balance={balance}
                setBalance={setBalance}
                isGenerating={isGenerating}
                walletBalance={walletBalance}
                isAuthenticated={isAuthenticated}
                error={error}
                handleStartFusion={handleStartFusion}
                fusionCost={FUSION_COST}
              />
            </CyberTerminalPanel>
          </div>
        </div>

        <footer className="mb-8 mt-12 text-center">
          <p className="text-[10px] font-black uppercase tracking-[0.3em] text-[#8F94A5]">
            {t('games.forge.powered_by', "Propulsé par le moteur génératif d'Animetix")}
          </p>
        </footer>
      </div>
    </div>
  );
};

export default ForgePage;
