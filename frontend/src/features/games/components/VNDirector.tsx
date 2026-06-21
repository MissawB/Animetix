import React from 'react';
import { RefreshCw, Trash2, Plus, Save } from 'lucide-react';
import { VNScene } from '../../../types';

interface VNDirectorProps {
  scenes: VNScene[];
  setScenes: (scenes: VNScene[]) => void;
  onRegenerate: (index: number) => void;
}

export const VNDirector: React.FC<VNDirectorProps> = ({ scenes, setScenes, onRegenerate }) => {
  const handleDialogueChange = (index: number, value: string) => {
    const newScenes = [...scenes];
    newScenes[index].dialogue = value;
    setScenes(newScenes);
  };

  const removeScene = (index: number) => {
    const newScenes = scenes.filter((_, i) => i !== index);
    setScenes(newScenes);
  };

  const addScene = () => {
    const lastScene = scenes[scenes.length - 1];
    setScenes([...scenes, { ...lastScene, dialogue: "Nouvelle ligne de dialogue..." }]);
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-right-10 duration-500">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-black italic manga-font uppercase">Director's Cut</h2>
          <p className="text-sm font-bold opacity-40 uppercase tracking-widest">Édition du script et de la mise en scène</p>
        </div>
        <button 
          onClick={addScene}
          className="bg-anime-accent text-black px-6 py-3 rounded-2xl font-black italic flex items-center gap-2 hover:scale-105 active:scale-95 transition-all shadow-lg"
        >
          <Plus className="w-5 h-5" /> Ajouter une Scène
        </button>
      </div>

      <div className="grid gap-4">
        {scenes.map((scene, index) => (
          <div key={index} className="bg-white dark:bg-anime-dark-card rounded-3xl p-6 border border-black/5 dark:border-white/5 shadow-xl flex gap-6 group">
            <div className="w-32 aspect-video rounded-xl overflow-hidden relative shrink-0">
              <img src={scene.background_url} className="w-full h-full object-cover" alt="" loading="lazy" decoding="async" />
              <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => onRegenerate(index)} className="p-2 bg-white rounded-full text-black hover:scale-110 transition-transform">
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="flex-1 space-y-4">
              <div className="flex justify-between">
                <input
                  aria-label="Nom du personnage"
                  value={scene.character_name}
                  onChange={(e) => {
                    const newScenes = [...scenes];
                    newScenes[index].character_name = e.target.value;
                    setScenes(newScenes);
                  }}
                  className="bg-transparent font-black italic text-anime-accent uppercase tracking-widest text-sm focus:outline-none"
                />
                <button onClick={() => removeScene(index)} className="text-anime-error opacity-0 group-hover:opacity-100 transition-opacity">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
              <textarea
                aria-label="Dialogue"
                value={scene.dialogue}
                onChange={(e) => handleDialogueChange(index, e.target.value)}
                className="w-full bg-black/5 dark:bg-white/5 border border-transparent focus:border-anime-accent/30 rounded-2xl p-4 text-sm font-medium leading-relaxed focus:outline-none transition-all resize-none h-24"
              />
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-end pt-8">
        <button className="bg-black text-white dark:bg-white dark:text-black px-10 py-5 rounded-2xl font-black italic text-lg shadow-2xl flex items-center gap-3 hover:scale-105 transition-all uppercase">
          <Save className="w-6 h-6" /> Sauvegarder le Script
        </button>
      </div>
    </div>
  );
};
