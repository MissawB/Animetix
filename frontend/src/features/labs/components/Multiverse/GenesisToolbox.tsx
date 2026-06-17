import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Zap, Shield, Wand2 } from 'lucide-react';

const SEEDS = [
  { id: 'Cyberpunk', label: 'Cyberpunk', icon: Zap, color: '#06b6d4' },
  { id: 'Fantasy', label: 'Fantasy', icon: Sparkles, color: '#a855f7' },
  { id: 'Sci-Fi', label: 'Sci-Fi', icon: Wand2, color: '#10b981' },
  { id: 'Steampunk', label: 'Steampunk', icon: Shield, color: '#f59e0b' },
];

type GenesisToolboxProps = object

export const GenesisToolbox: React.FC<GenesisToolboxProps> = () => {
  return (
    <motion.div 
      drag
      dragMomentum={false}
      className="absolute top-8 left-8 w-64 bg-black/60 backdrop-blur-2xl border border-white/10 rounded-3xl p-6 z-50 shadow-2xl"
    >
      <header className="mb-6 border-b border-white/5 pb-4">
        <h3 className="text-[10px] font-black uppercase tracking-[0.3em] text-red-500">Genesis Seeds</h3>
      </header>
      <div className="space-y-3">
        {SEEDS.map((seed) => (
          <div 
            key={seed.id}
            draggable
            onDragStart={(e) => {
              e.dataTransfer.setData('seed', seed.id);
            }}
            className="flex items-center gap-4 p-4 bg-white/5 rounded-2xl border border-white/5 hover:bg-white/10 transition-all cursor-grab active:cursor-grabbing group"
          >
            <seed.icon className="w-5 h-5" style={{ color: seed.color }} />
            <span className="text-xs font-black uppercase text-white/70 group-hover:text-white">{seed.label}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
};
