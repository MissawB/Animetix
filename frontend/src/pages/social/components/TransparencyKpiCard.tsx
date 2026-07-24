import React from 'react';

/** A single KPI tile in the Transparency dashboard header grid. The version tile
 *  uses a smaller, clamped value style via `valueClassName`. Voix données : la
 *  valeur est encrée en or, l'étiquette en graphite. */
export const TransparencyKpiCard: React.FC<{
  icon: React.ReactNode;
  value: React.ReactNode;
  label: string;
  valueClassName?: string;
}> = ({ icon, value, label, valueClassName = 'text-4xl font-black italic mb-1' }) => (
  <div className="flex flex-col items-center rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 text-center transition-colors hover:border-[#5D7FD3]/40">
    {icon}
    <span className={`font-manga text-[#FDB913] ${valueClassName}`}>{value}</span>
    <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">{label}</span>
  </div>
);
