import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Sparkles, Zap, Flame, Image as ImageIcon, Loader2, ChevronLeft, ChevronRight, ImageOff } from 'lucide-react';
import { CyberTerminalPanel } from '../../components/forge/CyberTerminalPanel';
import { GlitchText } from '../../components/forge/GlitchText';
import { useForge, FUSION_COST } from '../../hooks/useForge';
import { ForgeItemSelector } from '../../components/forge/ForgeItemSelector';
import { ForgeReactorPanel } from '../../components/forge/ForgeReactorPanel';
import { ForgeResultDisplay } from '../../components/forge/ForgeResultDisplay';

const ForgePage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  const {
    itemA, setItemA,
    itemB, setItemB,
    chaosLevel, setChaosLevel,
    balance, setBalance,
    artStyle, setArtStyle,
    styleDir, setStyleDir,
    isGenerating,
    fusionData,
    status,
    error,
    showConfetti,
    walletBalance,
    isAuthenticated,
    handleStartFusion,
    resetForge
  } = useForge();

  const ART_STYLES = useMemo(() => [
    { id: 'Cyberpunk', name: t('games.forge.styles.cyberpunk_name', 'Cyberpunk'), desc: t('games.forge.styles.cyberpunk_desc', 'Néons et technologie futuriste'), image: '/static/img/forge/styles/cyberpunk.jpg' },
    { id: 'Ukiyo-e', name: t('games.forge.styles.ukiyoe_name', 'Ukiyo-e'), desc: t('games.forge.styles.ukiyoe_desc', 'Estampe traditionnelle japonaise'), image: '/static/img/forge/styles/ukiyo-e.jpg' },
    { id: 'Noir & Blanc', name: t('games.forge.styles.manga_noir_name', 'Manga Noir'), desc: t('games.forge.styles.manga_noir_desc', 'Contraste élevé, trames classiques'), image: '/static/img/forge/styles/manga-noir.jpg' },
    { id: 'Vaporwave', name: t('games.forge.styles.vaporwave_name', 'Vaporwave'), desc: t('games.forge.styles.vaporwave_desc', 'Esthétique rétro 80s, couleurs pastel'), image: '/static/img/forge/styles/vaporwave.jpg' },
    { id: 'Steampunk', name: t('games.forge.styles.steampunk_name', 'Steampunk'), desc: t('games.forge.styles.steampunk_desc', 'Cuivre, vapeur et engrenages'), image: '/static/img/forge/styles/steampunk.png' },
    { id: 'Aquarelle', name: t('games.forge.styles.aquarelle_name', 'Aquarelle'), desc: t('games.forge.styles.aquarelle_desc', 'Douceur et transparences fluides'), image: '/static/img/forge/styles/aquarelle.png' },
    { id: 'Pixel Art', name: t('games.forge.styles.pixel_art_name', 'Pixel Art'), desc: t('games.forge.styles.pixel_art_desc', 'Rétro 8-bit, pixels et arcade'), image: '/static/img/forge/styles/pixel-art.jpg' },
    { id: 'Gothique', name: t('games.forge.styles.gothique_name', 'Gothique'), desc: t('games.forge.styles.gothique_desc', 'Victorien sombre et dramatique'), image: '/static/img/forge/styles/gothique.png' },
    { id: 'Mecha', name: t('games.forge.styles.mecha_name', 'Mecha'), desc: t('games.forge.styles.mecha_desc', 'Robots géants et science-fiction'), image: '/static/img/forge/styles/mecha.jpg' },
    { id: '', name: t('games.forge.styles.brut_name', 'Brut'), desc: t('games.forge.styles.brut_desc', 'Aucune esthétique imposée — fusion la plus fidèle'), image: '' },
  ], [t]);

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

  // --- RENDERING GENERATION ---
  if (isGenerating || (fusionData && !status?.completed)) {
    return (
      <div className="min-h-[80vh] flex items-center justify-center px-6">
        <div className="max-w-3xl w-full relative">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-yellow-400/20 blur-[120px] rounded-full animate-pulse" />

          <div className="bg-white/80 dark:bg-anime-dark-card/80 backdrop-blur-2xl rounded-[4rem] p-12 shadow-2xl border border-white/20 relative z-10 text-center overflow-hidden">
             <div className="absolute top-0 left-0 w-full h-2 bg-black/5 dark:bg-white/5">
                <div className="h-full bg-yellow-400 animate-[loading_2s_ease-in-out_infinite]" style={{ width: '30%' }} />
             </div>

             <div className="mb-12 relative">
                <div className="w-24 h-24 bg-yellow-400 rounded-3xl mx-auto flex items-center justify-center shadow-lg shadow-yellow-400/20 rotate-12 animate-bounce">
                    <Loader2 className="w-12 h-12 text-black animate-spin" />
                </div>
             </div>

             <h2 className="text-5xl font-black italic manga-font mb-6 tracking-tight">{t('games.forge.loading_title', 'ALCHIMIE EN COURS')}</h2>

             <div className="flex justify-center items-center gap-12 mb-12">
                <div className="group relative">
                    <div className="absolute -inset-2 bg-gradient-to-t from-yellow-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl blur-md" />
                    {itemA?.image_url ? (
                      <img src={itemA.image_url} className="w-28 h-40 object-cover rounded-2xl shadow-xl relative z-10 grayscale brightness-50" alt="" loading="lazy" decoding="async" />
                    ) : (
                      <div className="w-28 h-40 bg-black/20 rounded-2xl shadow-xl relative z-10 flex items-center justify-center">
                        <ImageIcon className="w-8 h-8 text-white/20" />
                      </div>
                    )}
                    <p className="mt-3 text-[10px] font-black uppercase opacity-40 max-w-[112px] truncate">{itemA?.title || itemA?.name}</p>
                </div>
                <div className="flex flex-col items-center">
                    <Sparkles className="w-10 h-10 text-yellow-400 animate-pulse mb-2" />
                    <div className="h-0.5 w-12 bg-gradient-to-r from-transparent via-yellow-400 to-transparent" />
                </div>
                <div className="group relative">
                    <div className="absolute -inset-2 bg-gradient-to-t from-blue-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl blur-md" />
                    {itemB?.image_url ? (
                      <img src={itemB.image_url} className="w-28 h-40 object-cover rounded-2xl shadow-xl relative z-10 grayscale brightness-50" alt="" loading="lazy" decoding="async" />
                    ) : (
                      <div className="w-28 h-40 bg-black/20 rounded-2xl shadow-xl relative z-10 flex items-center justify-center">
                        <ImageIcon className="w-8 h-8 text-white/20" />
                      </div>
                    )}
                    <p className="mt-3 text-[10px] font-black uppercase opacity-40 max-w-[112px] truncate">{itemB?.title || itemB?.name}</p>
                </div>
             </div>

             <div className="max-w-md mx-auto bg-black/5 dark:bg-white/5 p-6 rounded-3xl border border-black/10 dark:border-white/10">
                <p className="text-xs font-mono text-left opacity-60 overflow-hidden h-6">
                    {`> SEQ: INITIALIZING MULTIVERSAL BRIDGE...`}
                </p>
                <p className="text-xs font-mono text-left opacity-80 mt-1">
                    {`> STATUS: ${status?.status || "COLLECTING CONCEPTUAL DATA"}`}
                </p>
             </div>
          </div>
        </div>
      </div>
    );
  }

  // --- RENDERING RESULT ---
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

  // --- RENDERING CONFIGURATION (DEFAULT) ---
  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <div className="text-center mb-20 relative">
        <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-64 h-64 bg-yellow-400/10 blur-[100px] rounded-full" />
        <h1 className="text-8xl font-black italic manga-font mb-4 tracking-tighter leading-none">
          <GlitchText>{t('navbar.forge', 'LA FORGE')}</GlitchText>
        </h1>
        <div className="flex items-center justify-center gap-4 mb-4">
            <div className="h-px w-12 bg-black/10 dark:bg-white/10" />
            <p className="text-xs sm:text-sm font-black opacity-50 uppercase tracking-[0.25em] text-center">{t('games.forge.tagline', 'Fusionnez deux univers en une œuvre inédite')}</p>
            <div className="h-px w-12 bg-black/10 dark:bg-white/10" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 mb-16">
        <div className="lg:col-span-7 space-y-8">
            <CyberTerminalPanel>
                <h3 className="text-xl font-black italic manga-font mb-6 flex items-center gap-3">
                   <Zap className="w-5 h-5 text-yellow-400" /> {t('games.forge.universe_selector', "Sélecteur d'Univers")}
                </h3>
                <ForgeItemSelector
                  itemA={itemA}
                  setItemA={setItemA}
                  itemB={itemB}
                  setItemB={setItemB}
                />
            </CyberTerminalPanel>

            <CyberTerminalPanel>
                <h3 className="text-xl font-black italic manga-font mb-6 flex items-center gap-3">
                   <ImageIcon className="w-5 h-5 text-blue-400" /> {t('games.forge.visual_aesthetic', 'Esthétique Visuelle')}
                </h3>
                {(() => {
                    const len = ART_STYLES.length;
                    const idx = Math.max(0, ART_STYLES.findIndex((s) => s.id === artStyle));
                    const current = ART_STYLES[idx];
                    const prev = ART_STYLES[(idx - 1 + len) % len];
                    const next = ART_STYLES[(idx + 1) % len];
                    const visual = (s: (typeof ART_STYLES)[number]) =>
                        s.image ? (
                            <img src={s.image} alt={s.name} loading="lazy" decoding="async" className="absolute inset-0 w-full h-full object-cover" />
                        ) : (
                            <div className="absolute inset-0 bg-gradient-to-br from-navy-700 to-navy-950 flex items-center justify-center">
                                <ImageOff className="w-12 h-12 text-white/25" />
                            </div>
                        );
                    const slide = {
                        enter: (d: number) => ({ x: d >= 0 ? 220 : -220, opacity: 0 }),
                        center: { x: 0, opacity: 1 },
                        exit: (d: number) => ({ x: d >= 0 ? -220 : 220, opacity: 0 }),
                    };
                    return (
                      <div className="flex flex-col items-center">
                        <div className="relative h-[300px] w-full flex items-center justify-center overflow-hidden select-none">
                            {/* Neighbour: previous (set back, blurred) */}
                            <button
                                onClick={() => cycleStyle(-1)}
                                aria-label={t('games.forge.aria_prev_style_named', { defaultValue: 'Style précédent : {{name}}', name: prev.name })}
                                style={{ transform: 'translate(-50%, -50%) translateX(-148px) scale(0.78)' }}
                                className="absolute left-1/2 top-1/2 z-0 w-[200px] aspect-[3/4] rounded-3xl overflow-hidden opacity-45 blur-[3px] hover:opacity-70 hover:blur-[1px] transition-all duration-300"
                            >
                                {visual(prev)}
                                <div className="absolute inset-0 bg-black/40" />
                            </button>

                            {/* Neighbour: next (set back, blurred) */}
                            <button
                                onClick={() => cycleStyle(1)}
                                aria-label={t('games.forge.aria_next_style_named', { defaultValue: 'Style suivant : {{name}}', name: next.name })}
                                style={{ transform: 'translate(-50%, -50%) translateX(148px) scale(0.78)' }}
                                className="absolute left-1/2 top-1/2 z-0 w-[200px] aspect-[3/4] rounded-3xl overflow-hidden opacity-45 blur-[3px] hover:opacity-70 hover:blur-[1px] transition-all duration-300"
                            >
                                {visual(next)}
                                <div className="absolute inset-0 bg-black/40" />
                            </button>

                            {/* Featured (current) — swipeable */}
                            <AnimatePresence initial={false} custom={styleDir} mode="popLayout">
                                <motion.div
                                    key={current.id || 'brut'}
                                    custom={styleDir}
                                    variants={slide}
                                    initial="enter"
                                    animate="center"
                                    exit="exit"
                                    transition={{ x: { type: 'spring', stiffness: 320, damping: 32 }, opacity: { duration: 0.18 } }}
                                    drag="x"
                                    dragConstraints={{ left: 0, right: 0 }}
                                    dragElastic={0.7}
                                    onDragEnd={(_e, info) => {
                                        if (info.offset.x < -60) cycleStyle(1);
                                        else if (info.offset.x > 60) cycleStyle(-1);
                                    }}
                                    className="relative z-10 w-[210px] aspect-[3/4] rounded-3xl overflow-hidden border-2 border-yellow-400 ring-4 ring-yellow-400/20 shadow-2xl cursor-grab active:cursor-grabbing touch-pan-y"
                                >
                                    {visual(current)}
                                    <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/30 to-transparent pointer-events-none" />
                                    <span className="absolute top-3 left-3 bg-yellow-400 text-black text-[10px] font-black px-2.5 py-1 rounded-full uppercase tracking-tighter shadow pointer-events-none">{idx + 1}/{len}</span>
                                    <div className="absolute bottom-0 inset-x-0 p-4 text-left pointer-events-none">
                                        <div className="text-xl font-black italic uppercase text-white leading-none mb-1 drop-shadow-md">{current.name}</div>
                                        <div className="text-[11px] font-bold text-white/70 leading-tight">{current.desc}</div>
                                    </div>
                                </motion.div>
                            </AnimatePresence>

                            {/* Arrows on top */}
                            <button
                                onClick={() => cycleStyle(-1)}
                                aria-label={t('games.forge.aria_prev_style', 'Style précédent')}
                                className="absolute left-1 top-1/2 -translate-y-1/2 z-30 w-10 h-10 rounded-full bg-black/60 backdrop-blur text-white hover:bg-yellow-400 hover:text-black flex items-center justify-center transition-all active:scale-90 shadow-lg"
                            >
                                <ChevronLeft className="w-6 h-6" />
                            </button>
                            <button
                                onClick={() => cycleStyle(1)}
                                aria-label={t('games.forge.aria_next_style', 'Style suivant')}
                                className="absolute right-1 top-1/2 -translate-y-1/2 z-30 w-10 h-10 rounded-full bg-black/60 backdrop-blur text-white hover:bg-yellow-400 hover:text-black flex items-center justify-center transition-all active:scale-90 shadow-lg"
                            >
                                <ChevronRight className="w-6 h-6" />
                            </button>
                        </div>

                        <div className="flex flex-wrap justify-center gap-2 mt-5">
                            {ART_STYLES.map((s) => (
                                <button
                                    key={s.id || 'brut'}
                                    onClick={() => goToStyle(s.id)}
                                    aria-label={t('games.forge.aria_choose_style', { defaultValue: 'Choisir {{name}}', name: s.name })}
                                    aria-pressed={s.id === artStyle}
                                    className={`h-2 rounded-full transition-all ${s.id === artStyle ? 'w-6 bg-yellow-400' : 'w-2 bg-black/15 dark:bg-white/20 hover:bg-yellow-400/50'}`}
                                />
                            ))}
                        </div>
                      </div>
                    );
                })()}
            </CyberTerminalPanel>
        </div>

        <div className="lg:col-span-5 space-y-8">
            <CyberTerminalPanel className="sticky top-24">
                <h3 className="text-xl font-black italic manga-font mb-10 flex items-center gap-3">
                   <Flame className="w-5 h-5 text-red-500" /> {t('games.forge.reactor_settings', 'Paramètres du Réacteur')}
                </h3>
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

      {/* Footer Info */}
      <div className="text-center opacity-40 mt-12 mb-8">
         <p className="text-[10px] font-black tracking-[0.3em] uppercase">{t('games.forge.powered_by', "Propulsé par le moteur génératif d'Animetix")}</p>
      </div>
    </div>
  );
};

export default ForgePage;
