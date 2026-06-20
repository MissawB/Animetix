import React, { useState, useEffect } from 'react';
import { useReaderStore } from '../stores/useReaderStore';
import { WebtoonMode } from './modes/WebtoonMode';
import { TraditionalMode } from './modes/TraditionalMode';
import { InteractiveMode } from './modes/InteractiveMode';
import { Layout, Scroll, Sparkles, Settings as SettingsIcon, X } from 'lucide-react';

export const MangaReader: React.FC = () => {
  const { 
    mode, setMode,
    readingDirection, setReadingDirection,
    pageLayout, setPageLayout,
    splitWidePages, setSplitWidePages,
    imageWidth, setImageWidth,
    gapSize, setGapSize,
    brightness, setBrightness
  } = useReaderStore();
  
  const [showSettings, setShowSettings] = useState(false);

  // Keyboard navigation shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Escape closes settings panel
      if (e.key === 'Escape') {
        setShowSettings(false);
      }
      
      // Traditional / Interactive modes arrow keys navigation
      if (mode !== 'webtoon') {
        const state = useReaderStore.getState();
        if (state.pages.length === 0) return;
        
        if (e.key === 'ArrowRight') {
          if (state.readingDirection === 'rtl') {
            state.goToPrevPage();
          } else {
            state.goToNextPage();
          }
        } else if (e.key === 'ArrowLeft') {
          if (state.readingDirection === 'rtl') {
            state.goToNextPage();
          } else {
            state.goToPrevPage();
          }
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mode]);

  const renderMode = () => {
    switch (mode) {
      case 'webtoon': return <WebtoonMode />;
      case 'traditional': return <TraditionalMode />;
      case 'interactive': return <InteractiveMode />;
      default: return null;
    }
  };

  const modeIcons = {
    webtoon: <Scroll className="w-4 h-4" />,
    traditional: <Layout className="w-4 h-4" />,
    interactive: <Sparkles className="w-4 h-4" />
  };

  return (
    <div className="w-full h-full flex flex-col relative">
      <div className="flex justify-center items-center gap-4 mb-12 relative">
        <div className="bg-navy-900/80 backdrop-blur-md p-1.5 rounded-2xl flex gap-1 border border-white/10">
          {(['traditional', 'webtoon', 'interactive'] as const).map((m) => (
            <button 
              key={m} 
              onClick={() => setMode(m)}
              className={`px-6 py-2.5 rounded-xl flex items-center gap-2 text-xs font-black uppercase tracking-widest transition-all ${
                mode === m 
                ? 'bg-anime-accent text-white shadow-lg' 
                : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {modeIcons[m]}
              {m}
            </button>
          ))}
        </div>

        <div className="relative">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className={`p-3.5 rounded-2xl hover:bg-white/5 border transition-all ${
              showSettings 
                ? 'bg-anime-accent text-white border-anime-accent' 
                : 'text-gray-400 hover:text-white border-white/10 bg-navy-900/80 backdrop-blur-md'
            }`}
            title="Paramètres du lecteur"
          >
            <SettingsIcon className="w-5 h-5" />
          </button>

          {/* Settings Panel Popover */}
          <AnimatePresence>
            {showSettings && (
              <div className="absolute right-0 top-16 bg-[#090912]/95 backdrop-blur-2xl border border-white/10 p-6 rounded-2xl w-80 shadow-2xl z-50 text-white space-y-5">
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <h3 className="text-xs font-black uppercase tracking-wider text-anime-accent flex items-center gap-2">
                    <SettingsIcon className="w-4 h-4" /> Options de lecture
                  </h3>
                  <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-white">
                    <X className="w-4 h-4" />
                  </button>
                </div>

                {/* Reading Direction */}
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400">Sens de lecture</label>
                  <div className="grid grid-cols-2 gap-2 bg-[#0c0c1b] p-1 rounded-xl border border-white/5">
                    <button
                      onClick={() => setReadingDirection('rtl')}
                      className={`py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
                        readingDirection === 'rtl' ? 'bg-anime-accent text-white' : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Manga (RTL)
                    </button>
                    <button
                      onClick={() => setReadingDirection('ltr')}
                      className={`py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
                        readingDirection === 'ltr' ? 'bg-anime-accent text-white' : 'text-gray-400 hover:text-white'
                      }`}
                    >
                      Webtoon/BD (LTR)
                    </button>
                  </div>
                </div>

                {/* Page Layout (Only visible in traditional/interactive mode) */}
                {mode !== 'webtoon' && (
                  <>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black uppercase tracking-widest text-gray-400">Affichage</label>
                      <div className="grid grid-cols-2 gap-2 bg-[#0c0c1b] p-1 rounded-xl border border-white/5">
                        <button
                          onClick={() => setPageLayout('single')}
                          className={`py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
                            pageLayout === 'single' ? 'bg-anime-accent text-white' : 'text-gray-400 hover:text-white'
                          }`}
                        >
                          Simple page
                        </button>
                        <button
                          onClick={() => setPageLayout('double')}
                          className={`py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
                            pageLayout === 'double' ? 'bg-anime-accent text-white' : 'text-gray-400 hover:text-white'
                          }`}
                        >
                          Double page
                        </button>
                      </div>
                    </div>

                    {/* Split Wide Pages */}
                    <div className="flex items-center justify-between bg-[#0c0c1b]/40 border border-white/5 p-3 rounded-xl">
                      <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">Découper doubles pages</span>
                      <input
                        type="checkbox"
                        checked={splitWidePages}
                        onChange={(e) => setSplitWidePages(e.target.checked)}
                        className="w-4 h-4 accent-anime-accent cursor-pointer"
                      />
                    </div>
                  </>
                )}

                {/* Gap Size (Only visible in webtoon mode) */}
                {mode === 'webtoon' && (
                  <div className="space-y-2">
                    <label className="text-[10px] font-black uppercase tracking-widest text-gray-400">Espacement</label>
                    <div className="grid grid-cols-3 gap-2 bg-[#0c0c1b] p-1 rounded-xl border border-white/5">
                      {(['none', 'small', 'medium'] as const).map((size) => (
                        <button
                          key={size}
                          onClick={() => setGapSize(size)}
                          className={`py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
                            gapSize === size ? 'bg-anime-accent text-white' : 'text-gray-400 hover:text-white'
                          }`}
                        >
                          {size === 'none' ? 'Aucun' : size === 'small' ? 'Petit' : 'Moyen'}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Image Width */}
                <div className="space-y-2">
                  <label className="text-[10px] font-black uppercase tracking-widest text-gray-400">Largeur max</label>
                  <select
                    value={imageWidth}
                    onChange={(e) => setImageWidth(e.target.value as any)}
                    className="w-full bg-[#0c0c1b] border border-white/10 rounded-xl px-3 py-2 text-xs focus:outline-none focus:border-anime-accent font-semibold text-white"
                  >
                    <option value="scale-80">Étroite (80%)</option>
                    <option value="scale-100">Standard (100%)</option>
                    <option value="scale-xl">Optimisée (Max XL)</option>
                    <option value="scale-2xl">Large (Max 2XL)</option>
                    <option value="scale-full">Plein écran</option>
                  </select>
                </div>

                {/* Brightness Adjustment */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest text-gray-400">
                    <span>Luminosité</span>
                    <span className="text-anime-accent font-bold">{brightness}%</span>
                  </div>
                  <input
                    type="range"
                    min="20"
                    max="100"
                    value={brightness}
                    onChange={(e) => setBrightness(parseInt(e.target.value))}
                    className="w-full accent-anime-accent cursor-pointer"
                  />
                </div>
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
      
      <div 
        className="flex-1 overflow-y-auto"
        style={{ filter: `brightness(${brightness}%)` }}
      >
        {renderMode()}
      </div>
    </div>
  );
};

// Simple stub for AnimatePresence to avoid build errors if framer-motion imports are missing
const AnimatePresence: React.FC<{ children: React.ReactNode }> = ({ children }) => <>{children}</>;

