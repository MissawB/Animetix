import React from 'react';
import { Card } from '../../../components/ui/Card';

/** A single KPI tile in the Transparency dashboard header grid. The version tile
 *  uses a smaller, clamped value style via `valueClassName`. */
export const TransparencyKpiCard: React.FC<{
  icon: React.ReactNode;
  value: React.ReactNode;
  label: string;
  valueClassName?: string;
}> = ({ icon, value, label, valueClassName = 'text-4xl font-black italic mb-1' }) => (
  <Card className="!bg-navy-900/20 !border-white/5 p-8 flex flex-col items-center text-center transition-all hover:scale-105">
    {icon}
    <span className={valueClassName}>{value}</span>
    <span className="text-[10px] font-black opacity-30 uppercase tracking-widest">{label}</span>
  </Card>
);
