import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import { Box, Sliders, Info } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';

import { useTranslation } from 'react-i18next';

interface LatentPoint {
  x: number;
  y: number;
  z: number;
  title?: string;
  name?: string;
  cluster?: number;
}

const LatentSpacePage: React.FC = () => {
  const { t } = useTranslation();
  const [media, setMedia] = useState<string>('anime');
  const [type, setType] = useState<string>('thematic');

  const { data, isLoading } = useQuery<LatentPoint[]>({
    queryKey: ['latent-space', media, type],
    queryFn: () => apiClient(`/api/v1/latent-space/?media=${media}&type=${type}`),
  });

  const plotData = data ? [
    {
      x: data.map(d => d.x),
      y: data.map(d => d.y),
      z: data.map(d => d.z),
      mode: 'markers',
      type: 'scatter3d',
      text: data.map(d => d.title || d.name),
      marker: {
        size: 5,
        color: data.map(d => d.cluster || 0),
        colorscale: 'Viridis',
        opacity: 0.8
      }
    }
  ] : [];

  return (
    
      <div className="max-w-[1600px] mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row justify-between items-end mb-12 gap-6">
          <div>
              <h1 className="text-6xl font-black italic manga-font tracking-tighter uppercase">
              LATENT <span className="text-blue-500">SPACE</span>
              </h1>
              <p className="text-gray-500 font-bold uppercase tracking-widest mt-2 flex items-center gap-2">
                  <Box className="w-4 h-4 text-blue-500" /> Visualisation 3D des Embeddings IA
              </p>
          </div>

          <Card padding="sm" className="flex flex-wrap gap-4 border-none shadow-xl bg-white dark:bg-navy-800">
              <select 
                  value={media} 
                  onChange={(e) => setMedia(e.target.value)}
                  className="bg-gray-50 dark:bg-navy-900 border-0 rounded-xl px-6 py-3 font-black text-xs uppercase outline-none focus:ring-2 focus:ring-blue-500/20 cursor-pointer"
              >
                  <option value="anime">Anime</option>
                  <option value="manga">Manga</option>
                  <option value="character">Personnages</option>
              </select>
              <select 
                  value={type} 
                  onChange={(e) => setType(e.target.value)}
                  className="bg-gray-50 dark:bg-navy-900 border-0 rounded-xl px-6 py-3 font-black text-xs uppercase outline-none focus:ring-2 focus:ring-blue-500/20 cursor-pointer"
              >
                  <option value="thematic">Thématique</option>
                  <option value="visual">Visuel</option>
                  <option value="scenario">Scénario</option>
              </select>
          </Card>
        </div>

        <div className="bg-black rounded-[4rem] shadow-2xl overflow-hidden min-h-[700px] relative border-4 border-white/5">
          {isLoading ? (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm z-10">
                  <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6"></div>
                  <span className="text-white font-black italic uppercase tracking-[0.3em] animate-pulse">Projection Dimensionnelle...</span>
              </div>
          ) : (
              <Plot
                  data={plotData as any}
                  layout={{
                      width: undefined,
                      height: 700,
                      autosize: true,
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      scene: {
                          xaxis: { visible: false },
                          yaxis: { visible: false },
                          zaxis: { visible: false },
                      },
                      margin: { l: 0, r: 0, b: 0, t: 0 },
                      hovermode: 'closest',
                      font: { family: 'Montserrat', color: '#fff' }
                  }}
                  config={{ responsive: true, displayModeBar: false }}
                  style={{ width: '100%' }}
              />
          )}
        </div>

        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-8">
              <Card padding="lg" className="bg-brand-primary text-white border-none relative overflow-hidden shadow-brand-primary/20">
                  <Info className="w-20 h-20 absolute -right-4 -bottom-4 opacity-10" />
                  <h3 className="text-2xl font-black italic mb-4 uppercase">Comprendre l'Espace Latent</h3>
                  <p className="opacity-90 leading-relaxed text-sm font-bold italic">
                      Chaque point représente une œuvre convertie en vecteur mathématique par nos modèles de Deep Learning. 
                      Plus deux points sont proches, plus l'IA considère que ces œuvres partagent des similarités profondes.
                  </p>
              </Card>
              <Card padding="lg">
                  <h3 className="text-2xl font-black italic mb-6 uppercase manga-font">Navigation Tactique</h3>
                  <ul className="space-y-4">
                      <li className="flex items-center gap-4">
                          <Badge variant="neutral" className="p-2 rounded-xl"><Sliders className="w-4 h-4" /></Badge>
                          <span className="text-xs font-black uppercase opacity-60">Clic-Droit : Rotation de la sphère</span>
                      </li>
                      <li className="flex items-center gap-4">
                          <Badge variant="neutral" className="p-2 rounded-xl"><Sliders className="w-4 h-4" /></Badge>
                          <span className="text-xs font-black uppercase opacity-60">Molette : Zoom spatial</span>
                      </li>
                      <li className="flex items-center gap-4">
                          <Badge variant="neutral" className="p-2 rounded-xl"><Sliders className="w-4 h-4" /></Badge>
                          <span className="text-xs font-black uppercase opacity-60">Clic-Gauche : Déplacement de la grille</span>
                      </li>
                  </ul>
              </Card>
        </div>
      </div>
    
  );
};

export default LatentSpacePage;
