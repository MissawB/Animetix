import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface SectionHeaderProps {
  title: string;
  icon?: LucideIcon;
  iconClassName?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({
  title,
  icon: Icon,
  iconClassName,
}) => (
  <h3 className="text-2xl font-black italic uppercase tracking-widest flex items-center gap-3 mb-6">
    {Icon && <Icon className={`w-5 h-5 ${iconClassName ?? ''}`} aria-hidden="true" />}
    {title}
    <span className="h-px bg-white/10 flex-1" />
  </h3>
);
