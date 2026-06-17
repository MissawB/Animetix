import React, { useState } from 'react';
import _Plot from 'react-plotly.js';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from "../../utils/apiClient";
import { AnimatedPage } from "../../components/ui/AnimatedPage";
import { Card } from "../../components/ui/Card";
import { MapPin, ArrowLeft, Camera, Navigation, Globe } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { PlotlyEvent } from '../../types';

const Plot = (_Plot as unknown as { default: React.ComponentType<unknown> }).default || _Plot;

interface PilgrimageLocation {
  id: string;
  media_id: string;
  media_title: string;
  media_type: string;
  location_name: string;
  city: string;
  lat: number | null;
  lng: number | null;
  description: string;
  image?: string;
}

const SeichijunreiMapPage: React.FC = () => {
  const [selectedLoc, setSelectedLoc] = useState<PilgrimageLocation | null>(null);

  const { data: locations, isLoading } = useQuery<PilgrimageLocation[]>({
    queryKey: ['seichijunrei-locations'],
    queryFn: () => apiClient('/api/v1/explore/seichijunrei/'),
  });

  const handlePointClick = (event: PlotlyEvent) => {
    if (event.points && event.points[0]) {
      const loc = event.points[0].customdata as PilgrimageLocation;
      setSelectedLoc(loc);
    }
  };

  // Filter locations with coordinates
  const validLocations = locations?.filter(l => l.lat !== null && l.lng !== null) || [];

  const plotData: Array<Partial<Plotly.Data>> = validLocations.length > 0 ? [
    {
      type: 'scattergeo',
      mode: 'markers',
      lat: validLocations.map(l => l.lat as number),
      lon: validLocations.map(l => l.lng as number),
      customdata: validLocations,
      text: validLocations.map(l => `${l.location_name} (${l.media_title})`),
      hoverinfo: 'text',
      marker: {
        size: 12,
        color: '#fbbf24', // yellow-400
        line: {
          color: '#000',
          width: 2
        },
        opacity: 0.9,
        symbol: 'circle'
      }
    } as unknown as Partial<Plotly.Data>
  ] : [];

  return (
    <AnimatedPage>
      <div className="w-full h-[calc(100vh-64px)] bg-[#fdfdfd] dark:bg-black overflow-hidden flex flex-col lg:flex-row">
        
        {/* Sidebar / Info */}
        <div className="lg:w-[450px] h-full flex flex-col border-r border-gray-100 dark:border-white/5 bg-white dark:bg-[#0a0a0a] z-20 shadow-2xl relative">
          {/* Decorative Elements */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-yellow-400/5 blur-[60px] -mr-16 -mt-16 pointer-events-none" />
          
          <div className="p-8 border-b border-gray-100 dark:border-white/5 relative bg-white/50 dark:bg-black/50 backdrop-blur-md">
            <Link to="/explore/" className="inline-flex items-center gap-2 text-[10px] font-black uppercase text-gray-400 hover:text-yellow-500 transition-colors mb-8 no-underline tracking-widest">
              <ArrowLeft className="w-3 h-3" /> Retour à l'exploration
            </Link>
            <h1 className="text-5xl font-black italic manga-font tracking-tighter uppercase mb-2 leading-none">
              SEICHI <span className="text-yellow-400 text-glow">JUNREI</span>
            </h1>
            <p className="text-[10px] font-bold opacity-30 uppercase tracking-[0.2em] leading-relaxed max-w-xs">
              Cartographie algorithmique des lieux réels ayant inspiré les chefs-d'œuvre de l'animation.
            </p>
          </div>

          <div className="flex-grow overflow-y-auto custom-scrollbar p-8">
            <AnimatePresence mode="wait">
              {selectedLoc ? (
                <motion.div
                  key={selectedLoc.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="space-y-8"
                >
                  <div className="relative aspect-[4/3] rounded-[2.5rem] overflow-hidden shadow-2xl border-4 border-black group bg-gray-900">
                    {selectedLoc.image ? (
                        <img 
                          src={selectedLoc.image} 
                          alt={selectedLoc.media_title}
                          className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 opacity-80"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center opacity-20">
                            <Globe className="w-16 h-16" />
                        </div>
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent"></div>
                    <div className="absolute bottom-6 left-6 right-6">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="px-3 py-1 bg-yellow-400 text-black text-[9px] font-black uppercase rounded-full shadow-lg">
                            {selectedLoc.media_type}
                        </span>
                        <span className="px-3 py-1 bg-white/10 text-white text-[9px] font-black uppercase rounded-full backdrop-blur-md">
                            ID_{selectedLoc.media_id}
                        </span>
                      </div>
                      <h2 className="text-2xl font-black italic manga-font text-white uppercase leading-tight tracking-tighter">
                        {selectedLoc.media_title}
                      </h2>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="flex items-start gap-5">
                      <div className="p-4 bg-yellow-400 text-black rounded-[1.5rem] shadow-xl shadow-yellow-400/20 shrink-0">
                        <MapPin className="w-6 h-6" />
                      </div>
                      <div className="pt-1">
                        <h3 className="text-2xl font-black uppercase italic leading-none mb-2 tracking-tighter">{selectedLoc.location_name}</h3>
                        <p className="text-xs font-black opacity-30 uppercase tracking-widest">{selectedLoc.city}, JAPON</p>
                      </div>
                    </div>

                    <Card padding="lg" className="bg-gray-50 dark:bg-white/5 border-none rounded-[2rem] relative overflow-hidden group">
                      <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-100 transition-opacity">
                         <Camera className="w-5 h-5 text-yellow-400" />
                      </div>
                      <h4 className="text-[9px] font-black uppercase text-yellow-500 mb-4 tracking-[0.2em] flex items-center gap-2">
                         SCÈNE D'INSPIRATION
                      </h4>
                      <p className="text-sm font-bold leading-relaxed italic opacity-70">
                        "{selectedLoc.description || 'Information sémantique en cours de traitement...'}"
                      </p>
                    </Card>

                    <div className="pt-4 space-y-3">
                      <button 
                        onClick={() => window.open(`https://www.google.com/maps/dir/?api=1&destination=${selectedLoc.lat},${selectedLoc.lng}`, '_blank')}
                        className="w-full bg-black dark:bg-white text-white dark:text-black py-5 rounded-2xl font-black uppercase text-[10px] tracking-[0.3em] flex items-center justify-center gap-3 hover:scale-[1.02] active:scale-95 transition-all shadow-xl"
                      >
                        <Navigation className="w-4 h-4 fill-current" /> LANCER L'ITINÉRAIRE
                      </button>
                      <Link 
                        to={`/media/${selectedLoc.media_type}/${selectedLoc.media_id}`}
                        className="w-full border-2 border-black/10 dark:border-white/10 text-center py-4 rounded-2xl font-black uppercase text-[10px] tracking-[0.2em] block no-underline hover:bg-gray-50 dark:hover:bg-white/5 transition-colors"
                      >
                        VOIR L'ŒUVRE COMPLÈTE
                      </Link>
                    </div>
                  </div>
                </motion.div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-center py-20">
                  <div className="w-24 h-24 bg-gray-50 dark:bg-white/5 rounded-[2.5rem] flex items-center justify-center mb-8 animate-bounce-slow border-2 border-dashed border-gray-200 dark:border-white/10">
                    <MapPin className="w-10 h-10 text-yellow-400 opacity-40" />
                  </div>
                  <h3 className="text-xl font-black italic manga-font uppercase mb-3 tracking-tighter opacity-40">
                    Atlas Seichijunrei
                  </h3>
                  <p className="text-[10px] text-gray-400 font-black uppercase tracking-[0.2em] max-w-[200px] leading-relaxed">
                    Cliquez sur un marqueur pour explorer l'origine réelle du décor
                  </p>
                </div>
              )}
            </AnimatePresence>
          </div>

          {/* Stats Bar */}
          <div className="p-6 border-t border-gray-100 dark:border-white/5 bg-gray-50/50 dark:bg-black/40 flex justify-between items-center shrink-0">
             <div className="flex items-center gap-4">
                <div className="flex flex-col">
                    <span className="text-[8px] font-black uppercase opacity-30 leading-none">Localisations</span>
                    <span className="text-xs font-black italic text-yellow-500">{validLocations.length}</span>
                </div>
                <div className="h-6 w-px bg-black/5 dark:bg-white/5" />
                <div className="flex flex-col">
                    <span className="text-[8px] font-black uppercase opacity-30 leading-none">Précision</span>
                    <span className="text-xs font-black italic">GEODETIC_PROX</span>
                </div>
             </div>
             <div className="text-[8px] font-black uppercase opacity-20 tracking-tighter">
                ANIMETIX_MAP_SERVICE_V1.0
             </div>
          </div>
        </div>

        {/* Map Area */}
        <div className="flex-grow h-full bg-[#f0f2f5] dark:bg-[#050505] relative overflow-hidden">
          {isLoading && (
            <div className="absolute inset-0 z-30 flex flex-col items-center justify-center bg-white/80 dark:bg-black/80 backdrop-blur-md">
                <div className="w-16 h-16 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mb-6 shadow-[0_0_40px_rgba(251,191,36,0.2)]"></div>
                <span className="text-xs font-black italic uppercase tracking-[0.5em] text-yellow-500 animate-pulse">Synchronisation Atlas...</span>
            </div>
          )}

          {/* Map Overlay Textures */}
          <div className="absolute inset-0 opacity-10 pointer-events-none mix-blend-overlay z-10" style={{ backgroundImage: "url('https://www.transparenttextures.com/patterns/carbon-fibre.png')" }}></div>
          
          <div className="w-full h-full">
            <Plot
              data={plotData}
              onClick={handlePointClick}
              layout={{
                autosize: true,
                showlegend: false,
                geo: {
                  scope: 'asia',
                  center: { lat: 36.2, lon: 138.25 },
                  projection: { scale: 5, type: 'mercator' },
                  showland: true,
                  landcolor: '#ffffff',
                  subunitcolor: '#e5e7eb',
                  countrycolor: '#d1d5db',
                  showcountries: true,
                  showsubunits: true,
                  showlakes: true,
                  lakecolor: '#f0f9ff',
                  showocean: true,
                  oceancolor: '#f8fafc',
                  bgcolor: 'rgba(0,0,0,0)',
                  resolution: 50,
                  lonaxis: { range: [128, 146] },
                  lataxis: { range: [30, 46] }
                },
                margin: { l: 0, r: 0, t: 0, b: 0 },
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { family: 'Montserrat, sans-serif' }
              }}
              config={{
                responsive: true,
                displayModeBar: false,
                scrollZoom: true
              }}
              style={{ width: '100%', height: '100%' }}
            />
          </div>

          {/* Map Legend (Floating) */}
          <div className="absolute bottom-8 right-8 bg-white/80 dark:bg-black/80 backdrop-blur-xl border border-black/10 dark:border-white/10 p-5 rounded-[2rem] shadow-2xl z-20 hidden md:block">
              <div className="space-y-4">
                  <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-yellow-400 shadow-[0_0_10px_rgba(251,191,36,0.5)]" />
                      <span className="text-[9px] font-black uppercase tracking-widest opacity-60">Lieu d'Inspiration</span>
                  </div>
                  <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.5)] opacity-20" />
                      <span className="text-[9px] font-black uppercase tracking-widest opacity-20">Zone Dense (Pro)</span>
                  </div>
              </div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default SeichijunreiMapPage;
