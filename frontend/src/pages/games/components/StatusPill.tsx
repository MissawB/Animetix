import React from 'react';

export const StatusPill: React.FC<{ icon: React.ElementType; label: string; value: string }> = ({
  icon: Icon,
  label,
  value,
}) => (
  <div className="flex items-center gap-2.5 rounded-2xl border border-black/5 dark:border-white/10 bg-surface-card px-4 py-2.5 shadow-sm">
    <Icon className="w-4 h-4 opacity-40" />
    <div className="leading-none">
      <p className="text-[9px] font-black uppercase tracking-widest opacity-40">{label}</p>
      <p className="text-sm font-black mt-0.5">{value}</p>
    </div>
  </div>
);
