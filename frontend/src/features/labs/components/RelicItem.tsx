import React from 'react';
import { motion } from 'framer-motion';

interface RelicItemProps {
  id: string;
  title: string;
  sub: string;
  desc: string;
  color: string;
  glowColor: string;
  /** Kanji de la catégorie, gravé en filigrane derrière la relique. */
  glyph?: string;
  children: React.ReactNode;
  onClick: () => void;
}

export const RelicItem: React.FC<RelicItemProps> = ({
  id,
  title,
  sub,
  desc,
  color,
  glowColor,
  glyph,
  children,
  onClick,
}) => {
  return (
    <motion.button
      id={id}
      onClick={onClick}
      aria-label={title}
      className="flex flex-col items-center justify-center cursor-pointer group bg-transparent border-none outline-none p-0 text-inherit font-inherit"
      whileHover={{ y: -20, scale: 1.05 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
    >
      <div className="relative w-40 h-52 flex items-center justify-center">
        <div
          className={`absolute inset-0 blur-[40px] opacity-20 group-hover:opacity-60 transition-opacity rounded-full ${glowColor}`}
        />
        {glyph && (
          <span
            aria-hidden
            className={`absolute select-none text-[5.5rem] font-black leading-none opacity-[0.12] transition-opacity duration-500 group-hover:opacity-25 ${color}`}
          >
            {glyph}
          </span>
        )}
        <div
          className={`relative w-full h-full ${color} transition-all duration-500 group-hover:drop-shadow-[0_0_20px_currentColor]`}
        >
          {children}
        </div>
      </div>
      <div className="mt-8 text-center opacity-60 group-hover:opacity-100 transition-all transform group-hover:translate-y-2">
        <p className={`text-[10px] font-black uppercase tracking-widest mb-1 ${color}`}>{sub}</p>
        <h2 className="text-5xl font-black italic manga-font uppercase leading-none">{title}</h2>
        <p className="mt-4 text-[10px] font-bold opacity-30 uppercase tracking-widest">{desc}</p>
      </div>
    </motion.button>
  );
};
