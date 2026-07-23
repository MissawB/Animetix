import React from 'react';

/** Panneau d'atelier de la Forge (édition de nuit) : papier d'encre, coins
 *  print. Le nom historique est conservé pour éviter le churn d'imports. */
export const CyberTerminalPanel: React.FC<{ children: React.ReactNode; className?: string }> = ({
  children,
  className,
}) => (
  <div
    className={`rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-7 shadow-xl shadow-black/30 md:p-8 ${className ?? ''}`}
  >
    {children}
  </div>
);
