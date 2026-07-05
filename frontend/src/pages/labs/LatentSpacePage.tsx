import React, { useState } from 'react';
import _Plot from 'react-plotly.js';
import type * as Plotly from 'plotly.js';
import { Link } from 'react-router-dom';
import { Box,  Info, Globe, ArrowRight, Sparkles } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { motion, AnimatePresence } from 'framer-motion';



import { PlotlyEvent } from '../../types';

interface PlotProps {
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
  config?: Partial<Plotly.Config>;
  style?: React.CSSProperties;
  onClick?: (event: PlotlyEvent) => void;
}

const Plot = (_Plot as unknown as { default: React.ComponentType<PlotProps> }).default
  || (_Plot as unknown as React.ComponentType<PlotProps>);

interface LatentPoint {
  x: number;
  y: number;
  z: number;
  title?: string;
  name?: string;
  cluster?: number;
  image?: string;
  category?: string;
  year?: string;
  description?: string;
}

const LatentSpacePage: React.FC = () => {
  const [media, setMedia] = useState<string>('anime');
  const [type, setType] = useState<string>('thematic');
  const [selectedItem, setSelectedItem] = useState<LatentPoint | null>(null);

  const { data, isLoading } = useQuery<LatentPoint[]>({
    queryKey: ['latent-space', media, type],
    queryFn: () => apiClient(`/api/v1/latent-space/?media=${media}&type=${type}`),
  });

  const handlePointClick = (event: PlotlyEvent) => {
    if (event.points && event.points[0]) {
      const item = event.points[0].customdata as LatentPoint;
      if (item) {
        setSelectedItem(item);
      } else {
        const pointIndex = event.points[0].pointNumber;
        if (data && data[pointIndex]) {
          setSelectedItem(data[pointIndex]);
        }
      }
    }
  };

  const uniqueCategories = data ? Array.from(new Set(data.map(d => d.category || d.cluster || 'Unknown'))) : [];
  const getCategoryIndex = (category: string | number | undefined) => uniqueCategories.indexOf(category || 'Unknown');

  const plotData: Array<Partial<Plotly.Data>> = data ? [
    {
      x: data.map(d => d.x),
      y: data.map(d => d.y),
      z: data.map(d => d.z),
      customdata: data,
      mode: 'markers',
      type: 'scatter3d',
      text: data.map(d => d.title || d.name),
      hoverinfo: 'text',
      marker: {
        size: 4,
        color: data.map(d => getCategoryIndex(d.category || d.cluster)),
        cmin: 0,
        cmax: Math.max(1, uniqueCategories.length - 1),
        colorscale: 'Plasma', // More galactic colorscale (dark purple to bright yellow)
        opacity: 0.85,
        line: {
          color: 'rgba(255, 255, 255, 0.3)',
          width: 0.5
        }
      }
    } as unknown as Partial<Plotly.Data>
  ] : [];

  return (
    <AnimatedPage>
      <div className="relative w-full h-[calc(100vh-64px)] bg-black overflow-hidden flex flex-col lg:flex-row">
        
        {/* LEFT PANEL: 3D PLOT (Takes full remaining space) */}
        <div className="relative flex-grow h-full overflow-hidden bg-black">
          
          {/* Spatial Background Texture */}
          <div 
            className="absolute inset-0 opacity-40 mix-blend-screen pointer-events-none" 
            style={{ backgroundImage: "url('https://www.transparenttextures.com/patterns/stardust.png')", backgroundRepeat: 'repeat' }}
          ></div>
          
          {/* Subtle Radial Gradient for Deep Space feel */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-900/20 via-black/80 to-black pointer-events-none"></div>

          {/* OVERLAY CONTROLS (Top Left) */}
          <div className="absolute top-6 left-6 z-20 pointer-events-none">
            <div className="bg-black/60 backdrop-blur-md p-5 rounded-[1.5rem] border border-white/10 pointer-events-auto shadow-2xl max-w-[200px]">
                <h1 className="text-2xl font-black italic manga-font tracking-tighter uppercase text-white leading-none">
                  LATENT <span className="text-blue-500">SPACE</span>
                </h1>
                
                <div className="flex flex-col gap-3 mt-6">
                  <div className="flex flex-col gap-1">
                    <span className="text-[7px] font-black uppercase text-blue-400/70 ml-1">Domaine</span>
                    <select 
                        value={media} 
                        onChange={(e) => { setMedia(e.target.value); setSelectedItem(null); }}
                        className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 font-black text-[9px] uppercase outline-none focus:ring-1 focus:ring-blue-500/50 cursor-pointer text-white w-full"
                    >
                        <option value="anime">Anime</option>
                        <option value="manga">Manga</option>
                        <option value="character">Personnages</option>
                    </select>
                  </div>

                  <div className="flex flex-col gap-1">
                    <span className="text-[7px] font-black uppercase text-blue-400/70 ml-1">Axe d'analyse</span>
                    <select 
                        value={type} 
                        onChange={(e) => { setType(e.target.value); setSelectedItem(null); }}
                        className="bg-white/5 border border-white/10 rounded-lg px-3 py-2 font-black text-[9px] uppercase outline-none focus:ring-1 focus:ring-blue-500/50 cursor-pointer text-white w-full"
                    >
                        <option value="thematic">Thématique</option>
                        <option value="visual">Visuel</option>
                        <option value="scenario">Scénario</option>
                    </select>
                  </div>
                </div>
            </div>
          </div>

          {/* LOADING STATE */}
          {isLoading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm z-30">
                <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6 shadow-[0_0_40px_rgba(59,130,246,0.3)]"></div>
                <span className="text-white font-black italic uppercase tracking-[0.4em] text-xs animate-pulse">Projection Dimensionnelle...</span>
            </div>
          )}

          {/* PLOT CONTAINER */}
          <div className="w-full h-full cursor-crosshair">
            <Plot
                data={plotData as Plotly.Data[]}
                onClick={handlePointClick}
                layout={{
                    autosize: true,
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    scene: {
                        xaxis: { visible: false },
                        yaxis: { visible: false },
                        zaxis: { visible: false },
                        camera: {
                          eye: { x: 1.8, y: 1.8, z: 1.8 }
                        }
                    },
                    margin: { l: 0, r: 0, b: 0, t: 0 },
                    hovermode: 'closest',
                    font: { family: 'Montserrat', color: '#fff' }
                }}
                config={{ 
                  responsive: true, 
                  displayModeBar: false,
                  scrollZoom: true
                }}
                style={{ width: '100%', height: '100%' }}
            />
          </div>
        </div>

        {/* RIGHT PANEL: ANALYSIS CARD (Docked to the right) */}
        <div className="lg:w-[400px] h-full bg-[#1a1a2e] shadow-[-10px_0_30px_rgba(0,0,0,0.5)] border-l border-white/5 flex flex-col relative z-20">
          <AnimatePresence mode="wait">
            {selectedItem ? (
              <motion.div 
                key={selectedItem.title || selectedItem.name}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="flex flex-col h-full"
              >
                {/* Item Image Header */}
                <div className="relative w-full h-64 overflow-hidden bg-gray-900 shrink-0">
                  {selectedItem.image ? (
                    <img 
                      src={selectedItem.image} 
                      alt={selectedItem.title || selectedItem.name} 
                      className="w-full h-full object-cover opacity-60"
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Box className="w-12 h-12 text-white/20" />
                    </div>
                  )}
                  <div className="absolute inset-0 bg-gradient-to-t from-[#1a1a2e] via-[#1a1a2e]/40 to-transparent"></div>
                  
                  <div className="absolute bottom-6 left-6 right-6">
                    <Badge variant="primary" className="mb-3 bg-blue-500 text-white border-none px-3 py-1">
                      {selectedItem.category || 'Vecteur IA'}
                    </Badge>
                    <h2 className="text-2xl font-black italic manga-font text-white uppercase tracking-tighter leading-tight drop-shadow-lg">
                      {selectedItem.title || selectedItem.name}
                    </h2>
                  </div>
                </div>

                {/* Analysis Content */}
                <div className="p-6 flex-grow overflow-y-auto custom-scrollbar text-white">
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-white/5 p-4 rounded-2xl border border-white/5 text-center">
                      <span className="block text-[8px] font-black uppercase text-gray-400 mb-1 tracking-widest">Année</span>
                      <span className="text-sm font-black italic manga-font">{selectedItem.year || 'N/A'}</span>
                    </div>
                    <div className="bg-white/5 p-4 rounded-2xl border border-white/5 text-center">
                      <span className="block text-[8px] font-black uppercase text-gray-400 mb-1 tracking-widest">Cluster ID</span>
                      <span className="text-sm font-black italic manga-font">#{selectedItem.cluster || getCategoryIndex(selectedItem.category)}</span>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div>
                      <h4 className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-blue-500 mb-4">
                        <Info className="w-3 h-3" /> Analyse de Proximité
                      </h4>
                      <p className="text-sm leading-relaxed text-gray-400 font-medium italic">
                        Cette œuvre est positionnée dans l'espace selon ses caractéristiques **{type}**. Sa position vectorielle indique une forte affinité sémantique avec les clusters environnants.
                      </p>
                    </div>

                    <div className="pt-6 border-t border-white/5">
                      <Button 
                        as={Link} 
                        to={`/search/?q=${encodeURIComponent(selectedItem.title || selectedItem.name || '')}`}
                        className="w-full bg-blue-600 hover:bg-blue-700 text-white rounded-2xl py-4 font-black italic manga-font text-xs tracking-widest uppercase shadow-xl no-underline"
                      >
                        Explorer les Relations <ArrowRight className="ml-2 w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              </motion.div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full p-10 text-center">
                <div className="w-24 h-24 bg-white/5 rounded-full flex items-center justify-center mb-8 animate-bounce-slow">
                  <Globe className="w-10 h-10 text-blue-500 opacity-40" />
                </div>
                <h3 className="text-xl font-black italic manga-font text-white uppercase mb-4 tracking-tighter">
                  Prêt pour l'exploration ?
                </h3>
                <p className="text-sm text-gray-500 font-bold italic uppercase tracking-widest animate-pulse">
                  Cliquez sur un point lumineux dans l'espace pour l'analyser
                </p>
              </div>
            )}
          </AnimatePresence>

          {/* Bottom Footer Info */}
          <div className="p-6 bg-black/20 border-t border-white/5 mt-auto">
              <Link to="/graph/map/" className="flex items-center justify-center gap-3 no-underline text-[9px] font-black text-gray-400 hover:text-blue-500 transition-colors uppercase tracking-[0.2em]">
                <Globe className="w-3 h-3" /> Basculer vers la Vue Atlas
              </Link>
          </div>
        </div>

      </div>

      {/* Guide & Protocole */}
      <div className="bg-black text-white px-6 pt-24 pb-16">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card padding="lg" className="bg-black/40 border-blue-500/20 shadow-[0_0_50px_rgba(59,130,246,0.1)] relative overflow-hidden group">
                <div className="absolute -right-12 -bottom-12 opacity-5 group-hover:opacity-10 transition-opacity">
                    <Globe className="w-64 h-64 text-blue-500" />
                </div>
                <h4 className="text-xl font-black italic manga-font uppercase mb-4 flex items-center gap-3">
                    <Sparkles className="w-5 h-5 text-blue-400" /> Guide de l'Espace Latent
                </h4>
                <div className="space-y-4 relative z-10">
                    <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                        <span className="text-blue-400">Le Concept :</span> Chaque point lumineux est un anime, un manga ou un personnage. Sa position reflète la façon dont l'IA comprend l'œuvre : deux points proches se ressemblent.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                        <span className="text-blue-400">La Navigation :</span> Faites pivoter la carte à la souris, zoomez à la molette, puis cliquez sur un point pour ouvrir sa fiche d'analyse dans le panneau de droite.
                    </p>
                    <p className="text-xs font-bold uppercase tracking-wider text-white/60 leading-relaxed">
                        <span className="text-blue-400">Les Filtres :</span> Changez le domaine (anime, manga, personnages) et l'axe d'analyse (thématique, visuel, scénario) pour recharger la carte sous un autre angle.
                    </p>
                </div>
            </Card>

            <div className="p-12 rounded-[4rem] bg-gradient-to-br from-blue-600/10 to-transparent border border-white/5 flex flex-col justify-center text-center">
                <p className="text-sm font-black uppercase tracking-[0.15em] italic leading-relaxed text-blue-200/60">
                    Visualisation exploratoire du catalogue : des embeddings haute dimension sont projetés en 3 dimensions puis rendus en nuage de points interactif (Plotly scatter3d). <br />
                    La proximité spatiale traduit la similarité sémantique des vecteurs ; les couleurs regroupent les clusters ou catégories détectés.
                </p>
            </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default LatentSpacePage;
