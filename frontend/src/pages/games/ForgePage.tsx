import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Zap, Flame, Image as ImageIcon, Loader2, RefreshCw, Heart, Share2, Info, X, Film, Check } from 'lucide-react';
import { SearchBar } from "../../components/SearchBar";
import { CyberTerminalPanel } from '../../components/forge/CyberTerminalPanel';
import { GlitchText } from '../../components/forge/GlitchText';
import { CyberSlider } from '../../components/forge/CyberSlider';
import { CyberButton } from '../../components/forge/CyberButton';
import { startFusion, getFusionStatus, FusionResponse, FusionStatus } from '../../api';

const ART_STYLES = [
  { id: 'Cyberpunk', name: 'Cyberpunk', desc: 'Néons et technologie futuriste', image: '/static/img/forge/styles/cyberpunk.jpg' },
  { id: 'Ukiyo-e', name: 'Ukiyo-e', desc: 'Estampe traditionnelle japonaise', image: '/static/img/forge/styles/ukiyo-e.jpg' },
  { id: 'Noir & Blanc', name: 'Manga Noir', desc: 'Contraste élevé, trames classiques', image: '/static/img/forge/styles/manga-noir.jpg' },
  { id: 'Vaporwave', name: 'Vaporwave', desc: 'Esthétique rétro 80s, couleurs pastel', image: '/static/img/forge/styles/vaporwave.jpg' },
  { id: 'Steampunk', name: 'Steampunk', desc: 'Cuivre, vapeur et engrenages', image: '/static/img/forge/styles/steampunk.png' },
  { id: 'Aquarelle', name: 'Aquarelle', desc: 'Douceur et transparences fluides', image: '/static/img/forge/styles/aquarelle.png' },
];

import { SearchItem } from '../../types';

// ...

const ForgePage: React.FC = () => {
  const navigate = useNavigate();
  const [itemA, setItemA] = useState<SearchItem | null>(null);
  const [itemB, setItemB] = useState<SearchItem | null>(null);
  const [chaosLevel, setChaosLevel] = useState<number>(50);
  const [balance, setBalance] = useState<number>(50);
  const [artStyle, setArtStyle] = useState<string>('Cyberpunk');
  
  const [isGenerating, setIsLoading] = useState<boolean>(false);
  const [fusionData, setFusionData] = useState<FusionResponse | null>(null);
  const [status, setStatus] = useState<FusionStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [, setShowConfetti] = useState(false);

  const handleStartFusion = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await startFusion({
        title_A: itemA?.title || itemA?.name,
        title_B: itemB?.title || itemB?.name,
        chaos_level: chaosLevel,
        universe_balance: balance,
        art_style: artStyle
      });
      setFusionData(res);
    } catch (_err) {
      setError("Le réacteur de fusion a surchauffé. Réessayez plus tard.");
      setIsLoading(false);
    }
  };

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (fusionData && !status?.completed) {
      interval = setInterval(async () => {
        try {
          const res = await getFusionStatus(fusionData.task_id, fusionData.fusion_id);
          setStatus(res);
          if (res.completed) {
            setIsLoading(false);
            setShowConfetti(true);
            clearInterval(interval);
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [fusionData, status, setShowConfetti]);

  const resetForge = () => {
    setFusionData(null);
    setStatus(null);
    setItemA(null);
    setItemB(null);
    setIsLoading(false);
    setShowConfetti(false);
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

             <h2 className="text-5xl font-black italic manga-font mb-6 tracking-tight">ALCHIMIE EN COURS</h2>
             
             <div className="flex justify-center items-center gap-12 mb-12">
                <div className="group relative">
                    <div className="absolute -inset-2 bg-gradient-to-t from-yellow-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl blur-md" />
                    <img src={itemA?.image_url} className="w-28 h-40 object-cover rounded-2xl shadow-xl relative z-10 grayscale brightness-50" alt="" loading="lazy" decoding="async" />
                    <p className="mt-3 text-[10px] font-black uppercase opacity-40 max-w-[112px] truncate">{itemA?.title || itemA?.name}</p>
                </div>
                <div className="flex flex-col items-center">
                    <Sparkles className="w-10 h-10 text-yellow-400 animate-pulse mb-2" />
                    <div className="h-0.5 w-12 bg-gradient-to-r from-transparent via-yellow-400 to-transparent" />
                </div>
                <div className="group relative">
                    <div className="absolute -inset-2 bg-gradient-to-t from-blue-400 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl blur-md" />
                    <img src={itemB?.image_url} className="w-28 h-40 object-cover rounded-2xl shadow-xl relative z-10 grayscale brightness-50" alt="" loading="lazy" decoding="async" />
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
      <div className="max-w-7xl mx-auto px-6 py-12 animate-in fade-in zoom-in-95 duration-700">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          
          <div className="lg:col-span-5 relative group">
             <div className="absolute -inset-4 bg-yellow-400/20 blur-3xl rounded-[4rem] opacity-50 group-hover:opacity-100 transition-opacity" />
             <div className="relative overflow-hidden rounded-[3.5rem] shadow-2xl border-8 border-white dark:border-anime-dark-card transform -rotate-1 hover:rotate-0 transition-transform duration-500">
                {status.image_url ? (
                  <img src={status.image_url} className="w-full aspect-[3/4] object-cover scale-105 group-hover:scale-100 transition-transform duration-700" alt="Fusion" loading="lazy" decoding="async" />
                ) : (
                  <div className="w-full aspect-[3/4] bg-anime-dark-bg flex flex-col items-center justify-center gap-4">
                     <ImageIcon className="w-20 h-20 text-white/10" />
                     <p className="text-xs font-black opacity-20 uppercase tracking-widest">Image non générée</p>
                  </div>
                )}
                
                <div className="absolute top-8 left-8 flex flex-col gap-2">
                   <span className="bg-black/80 backdrop-blur-md text-white text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-tighter">
                      Style: {artStyle}
                   </span>
                   <span className="bg-yellow-400 text-black text-[10px] font-black px-4 py-1.5 rounded-full uppercase tracking-tighter shadow-lg">
                      Chaos: {chaosLevel}%
                   </span>
                </div>
             </div>
             
             <div className="absolute -bottom-8 -right-4 bg-white dark:bg-anime-dark-card p-6 rounded-3xl shadow-2xl border border-gray-100 dark:border-white/5 max-w-[280px] transform rotate-3">
                <div className="flex items-center gap-3 mb-2">
                    <Sparkles className="w-5 h-5 text-yellow-400" />
                    <span className="text-[10px] font-black opacity-40 uppercase tracking-widest">NOUVEL ARCHÉTYPE</span>
                </div>
                <h3 className="text-xl font-black italic manga-font leading-tight">
                    {itemA?.title || itemA?.name} <span className="text-yellow-400 text-sm">×</span> {itemB?.title || itemB?.name}
                </h3>
             </div>
          </div>

          <div className="lg:col-span-7 space-y-10 pt-8 lg:pt-0">
             <div>
                <h1 className="text-7xl font-black italic manga-font leading-[0.8] tracking-tighter uppercase mb-4">
                   FUSION <span className="text-yellow-400">RÉUSSIE</span>
                </h1>
                <p className="text-xl font-bold opacity-30 uppercase tracking-[0.2em]">Une nouvelle réalité a été forgée dans le nexus.</p>
             </div>

             <div className="bg-white/50 dark:bg-anime-dark-card/50 backdrop-blur-xl p-10 rounded-[3rem] shadow-xl border border-white dark:border-white/5 relative group">
                <div className="absolute -top-4 -left-4 bg-black text-white px-6 py-2 text-xs font-black uppercase tracking-widest rounded-2xl shadow-lg group-hover:-translate-y-1 transition-transform">
                   SYNOPSIS GÉNÉRÉ PAR L'IA
                </div>
                <div className="prose dark:prose-invert max-w-none">
                    <p className="text-2xl leading-relaxed italic font-medium opacity-90 first-letter:text-5xl first-letter:font-black first-letter:text-yellow-400 first-letter:mr-3 first-letter:float-left whitespace-pre-wrap">
                        {status.scenario}
                    </p>
                </div>
             </div>

             <div className="flex flex-wrap gap-4">
                <button 
                   onClick={() => navigate(`/forge/vn/${fusionData?.fusion_id}/`)}
                   className="flex-1 min-w-[200px] bg-yellow-400 text-black py-5 px-8 rounded-2xl font-black italic text-lg hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3 uppercase shadow-xl"
                >
                   <Film className="w-6 h-6" />
                   Transformer en Visual Novel
                </button>
                <button 
                   onClick={resetForge}
                   className="flex-1 min-w-[200px] bg-black text-white dark:bg-white dark:text-black py-5 px-8 rounded-2xl font-black italic text-lg hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-3 uppercase shadow-xl"
                >
                   <RefreshCw className="w-6 h-6" />
                   Retourner à la Forge
                </button>
                <div className="flex gap-4">
                    <button className="w-16 h-16 bg-white dark:bg-anime-dark-card flex items-center justify-center rounded-2xl shadow-lg hover:text-red-500 hover:scale-110 transition-all border border-black/5 dark:border-white/5">
                        <Heart className="w-8 h-8" />
                    </button>
                    <button className="w-16 h-16 bg-white dark:bg-anime-dark-card flex items-center justify-center rounded-2xl shadow-lg hover:text-blue-500 hover:scale-110 transition-all border border-black/5 dark:border-white/5">
                        <Share2 className="w-8 h-8" />
                    </button>
                </div>
             </div>
          </div>
        </div>
      </div>
    );
  }

  // --- RENDERING CONFIGURATION (DEFAULT) ---
  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <div className="text-center mb-20 relative">
        <div className="absolute -top-20 left-1/2 -translate-x-1/2 w-64 h-64 bg-yellow-400/10 blur-[100px] rounded-full" />
        <h1 className="text-8xl font-black italic manga-font mb-4 tracking-tighter leading-none">
          <GlitchText>LA FORGE</GlitchText>
        </h1>
        <div className="flex items-center justify-center gap-4 mb-4">
            <div className="h-px w-12 bg-black/10 dark:bg-white/10" />
            <p className="text-xs sm:text-sm font-black opacity-50 uppercase tracking-[0.25em] text-center">Fusionnez deux univers en une œuvre inédite</p>
            <div className="h-px w-12 bg-black/10 dark:bg-white/10" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 mb-16">
        
        <div className="lg:col-span-7 space-y-8">
            <CyberTerminalPanel>
                <h3 className="text-xl font-black italic manga-font mb-6 flex items-center gap-3">
                   <Zap className="w-5 h-5 text-yellow-400" /> Sélecteur d'Univers
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative">
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <label htmlFor="univers-alpha" className="text-[10px] font-black uppercase tracking-widest opacity-70">Univers Alpha</label>
                            {itemA && <button onClick={() => setItemA(null)} className="text-[10px] font-bold text-red-500 hover:underline flex items-center gap-1"><X className="w-2 h-2" /> Effacer</button>}
                        </div>
                        <SearchBar id="univers-alpha" onSelect={setItemA} placeholder="Rechercher..." />
                        
                        <div className="h-[180px] relative overflow-hidden rounded-3xl bg-black/5 dark:bg-white/5 border border-dashed border-black/10 dark:border-white/10 flex items-center justify-center group transition-all">
                            {itemA ? (
                                <>
                                    <img src={itemA.image_url} className="absolute inset-0 w-full h-full object-cover brightness-50 group-hover:scale-110 transition-transform duration-500" alt="" loading="lazy" decoding="async" />
                                    <div className="relative z-10 text-center p-4">
                                        <div className="font-black italic text-white uppercase drop-shadow-md leading-tight mb-1">{itemA.title || itemA.name}</div>
                                        <div className="text-[9px] bg-white/20 backdrop-blur-md text-white font-bold px-2 py-0.5 rounded-full inline-block uppercase">{itemA.type}</div>
                                    </div>
                                </>
                            ) : (
                                <div className="text-center opacity-40 group-hover:opacity-70 transition-opacity">
                                    <div className="w-12 h-12 bg-black/10 dark:bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-2">
                                        <Info className="w-6 h-6" />
                                    </div>
                                    <span className="text-[10px] font-black uppercase tracking-widest">Choisir l'origine</span>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="hidden md:flex absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 h-12 bg-yellow-400 text-black rounded-2xl items-center justify-center z-20 shadow-lg shadow-yellow-400/40 ring-4 ring-cyberpunk-bg rotate-12">
                        <Sparkles className="w-6 h-6" strokeWidth={2.5} />
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <label htmlFor="univers-beta" className="text-[10px] font-black uppercase tracking-widest opacity-70">Univers Bêta</label>
                            {itemB && <button onClick={() => setItemB(null)} className="text-[10px] font-bold text-red-500 hover:underline flex items-center gap-1"><X className="w-2 h-2" /> Effacer</button>}
                        </div>
                        <SearchBar id="univers-beta" onSelect={setItemB} placeholder="Rechercher..." />
                        
                        <div className="h-[180px] relative overflow-hidden rounded-3xl bg-black/5 dark:bg-white/5 border border-dashed border-black/10 dark:border-white/10 flex items-center justify-center group transition-all">
                            {itemB ? (
                                <>
                                    <img src={itemB.image_url} className="absolute inset-0 w-full h-full object-cover brightness-50 group-hover:scale-110 transition-transform duration-500" alt="" loading="lazy" decoding="async" />
                                    <div className="relative z-10 text-center p-4">
                                        <div className="font-black italic text-white uppercase drop-shadow-md leading-tight mb-1">{itemB.title || itemB.name}</div>
                                        <div className="text-[9px] bg-white/20 backdrop-blur-md text-white font-bold px-2 py-0.5 rounded-full inline-block uppercase">{itemB.type}</div>
                                    </div>
                                </>
                            ) : (
                                <div className="text-center opacity-40 group-hover:opacity-70 transition-opacity">
                                    <div className="w-12 h-12 bg-black/10 dark:bg-white/10 rounded-2xl flex items-center justify-center mx-auto mb-2">
                                        <Info className="w-6 h-6" />
                                    </div>
                                    <span className="text-[10px] font-black uppercase tracking-widest">Choisir l'origine</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </CyberTerminalPanel>

            <CyberTerminalPanel>
                <div className="flex items-center justify-between mb-6">
                   <h3 className="text-xl font-black italic manga-font flex items-center gap-3">
                      <ImageIcon className="w-5 h-5 text-blue-400" /> Esthétique Visuelle
                   </h3>
                   <span className="text-[9px] font-black uppercase tracking-widest opacity-40 hidden sm:block">Faites défiler →</span>
                </div>
                <div className="flex gap-4 overflow-x-auto custom-scrollbar pb-3 -mx-1 px-1 snap-x snap-mandatory">
                    {ART_STYLES.map(style => {
                        const selected = artStyle === style.id;
                        return (
                        <button
                            key={style.id}
                            onClick={() => setArtStyle(style.id)}
                            aria-pressed={selected}
                            title={style.desc}
                            className={`group/style relative w-40 flex-shrink-0 snap-start aspect-[3/4] rounded-3xl overflow-hidden border-2 transition-all duration-300 ${selected ? 'border-yellow-400 ring-4 ring-yellow-400/20 scale-[1.02]' : 'border-transparent opacity-70 hover:opacity-100'}`}
                        >
                            <img src={style.image} alt={style.name} loading="lazy" decoding="async" className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover/style:scale-110" />
                            <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/30 to-transparent" />
                            {selected && (
                                <div className="absolute top-2.5 right-2.5 w-6 h-6 rounded-full bg-yellow-400 text-black flex items-center justify-center shadow-lg">
                                    <Check className="w-4 h-4" strokeWidth={3} />
                                </div>
                            )}
                            <div className="absolute bottom-0 inset-x-0 p-3 text-left">
                                <div className="font-black italic text-sm uppercase text-white leading-none mb-1 drop-shadow-md">{style.name}</div>
                                <div className="text-[9px] font-bold text-white/70 leading-tight line-clamp-2">{style.desc}</div>
                            </div>
                        </button>
                        );
                    })}
                </div>
            </CyberTerminalPanel>
        </div>

        <div className="lg:col-span-5 space-y-8">
            <CyberTerminalPanel className="sticky top-24">
                <h3 className="text-xl font-black italic manga-font mb-10 flex items-center gap-3">
                   <Flame className="w-5 h-5 text-red-500" /> Paramètres du Réacteur
                </h3>

                <div className="space-y-12">
                    <div>
                        <div className="flex justify-between items-end mb-4">
                           <div className="space-y-1">
                               <span className="text-xs font-black uppercase tracking-widest text-red-500">Niveau de Chaos</span>
                               <p className="text-[10px] font-bold opacity-55 max-w-[180px]">Définit le degré d'imprévisibilité de la fusion.</p>
                           </div>
                           <span className="text-2xl font-black italic manga-font text-red-500">{chaosLevel}%</span>
                        </div>
                        <div className="relative group pt-4">
                            <CyberSlider 
                                min={0} max={100} value={chaosLevel} 
                                onChange={setChaosLevel} 
                                color="magenta"
                            />
                            <div className="flex justify-between mt-3 text-[9px] font-black uppercase opacity-45">
                                <span>Cohérent</span>
                                <span>Distordu</span>
                                <span>Entropie</span>
                            </div>
                        </div>
                    </div>

                    <div>
                        <div className="flex justify-between items-end mb-4">
                           <div className="space-y-1">
                               <span className="text-xs font-black uppercase tracking-widest text-blue-500">Équilibre des ADN</span>
                               <p className="text-[10px] font-bold opacity-55 max-w-[180px]">Quel univers doit dominer la structure globale ?</p>
                           </div>
                           <span className="text-2xl font-black italic manga-font text-blue-500">{balance}%</span>
                        </div>
                        <div className="relative group pt-4">
                            <CyberSlider 
                                min={0} max={100} value={balance} 
                                onChange={setBalance} 
                                color="cyan"
                            />
                            <div className="flex justify-between mt-3 text-[9px] font-black uppercase opacity-45">
                                <span>Origine A</span>
                                <span>Hybride</span>
                                <span>Origine B</span>
                            </div>
                        </div>
                    </div>

                    <CyberButton
                        onClick={() => !(!itemA || !itemB || isGenerating) && handleStartFusion()}
                        className={`w-full py-8 rounded-[2.5rem] font-black italic text-3xl shadow-2xl transition-all duration-300 flex items-center justify-center gap-4 uppercase ${(!itemA || !itemB || isGenerating) ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                        <Sparkles className="w-8 h-8" />
                        Forger la Réalité
                    </CyberButton>
                    
                    {error && <div className="text-red-500 text-center text-xs font-black uppercase bg-red-500/10 p-4 rounded-2xl animate-bounce">{error}</div>}
                </div>
            </CyberTerminalPanel>
        </div>
      </div>

      {/* Footer Info */}
      <div className="text-center opacity-40 mt-12 mb-8">
         <p className="text-[10px] font-black tracking-[0.3em] uppercase">Propulsé par le moteur génératif d'Animetix</p>
      </div>
    </div>
  );
};

export default ForgePage;


