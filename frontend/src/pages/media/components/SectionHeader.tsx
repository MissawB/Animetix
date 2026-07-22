import React from 'react';
import type { LucideIcon } from 'lucide-react';

interface SectionHeaderProps {
  title: string;
  /** Conservé pour compatibilité d'API ; la rubrique est marquée par la barre d'encre. */
  icon?: LucideIcon;
  iconClassName?: string;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({ title }) => (
  <h3 className="mb-6 flex items-center gap-4 font-manga text-xl font-black uppercase italic tracking-wide text-[#F4F1E8] md:text-2xl">
    <span className="h-6 w-1.5 flex-none bg-[#E8442B]" aria-hidden />
    {title}
    <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
  </h3>
);
