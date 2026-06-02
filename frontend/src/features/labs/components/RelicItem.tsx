import React from 'react';
import { motion } from 'framer-motion';

interface RelicItemProps {
  id: string;
  title: string;
  sub: string;
  desc: string;
  color: string;
  glowColor: string;
  children: React.ReactNode;
  onClick: () => void;
}

export const RelicItem: React.FC<RelicItemProps> = ({ 
  title, sub, desc, color, glowColor, children, onClick 
}) => {
  return (
    <motion.div 
      onClick={onClick}
      className="flex flex-col items-center justify-center cursor-pointer group"
      whileHover={{ y: -20, scale: 1.05 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <div className="relative w-60 h-80 flex items-center justify-center">
        <div className={`absolute inset-0 blur-[40px] opacity-20 group-hover:opacity-60 transition-opacity rounded-full ${glowColor}`} />
        <div className={`w-full h-full ${color} transition-all duration-500 group-hover:drop-shadow-[0_0_20px_currentColor]`}>
          {children}
        </div>
      </div>
      <div className="mt-8 text-center opacity-60 group-hover:opacity-100 transition-all transform group-hover:translate-y-2">
        <p className={`text-[10px] font-black uppercase tracking-widest mb-1 ${color}`}>{sub}</p>
        <h2 className="text-5xl font-black italic manga-font uppercase leading-none">{title}</h2>
        <p className="mt-4 text-[10px] font-bold opacity-30 uppercase tracking-widest">{desc}</p>
      </div>
    </motion.div>
  );
};
