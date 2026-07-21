import React from 'react';
import type { PlateSize } from '../loreCartography';

export const Graticule: React.FC<{ view: PlateSize }> = ({ view: VIEW }) => (
  <g className="text-white/[0.05]">
    {Array.from({ length: 11 }, (_, i) => (
      <line
        key={`v${i}`}
        x1={(i * VIEW.w) / 10}
        y1={0}
        x2={(i * VIEW.w) / 10}
        y2={VIEW.h}
        stroke="currentColor"
        strokeWidth={1}
      />
    ))}
    {Array.from({ length: 7 }, (_, i) => (
      <line
        key={`h${i}`}
        x1={0}
        y1={(i * VIEW.h) / 6}
        x2={VIEW.w}
        y2={(i * VIEW.h) / 6}
        stroke="currentColor"
        strokeWidth={1}
      />
    ))}
  </g>
);

export const Plate: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div
    className={`relative overflow-hidden rounded-[2rem] border border-anime-accent/15 bg-[#0a0a12] ${className}`}
  >
    <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-anime-accent/[0.07] blur-[90px]" />
    <div className="pointer-events-none absolute -bottom-32 -right-16 h-80 w-80 rounded-full bg-anime-accent/[0.05] blur-[110px]" />
    {children}
  </div>
);
