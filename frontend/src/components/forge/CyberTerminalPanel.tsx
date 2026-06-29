import React from 'react';

export const CyberTerminalPanel: React.FC<{children: React.ReactNode, className?: string}> = ({children, className}) => (
  <div className={`backdrop-blur-md bg-cyberpunk-panel border border-cyberpunk-panelBorder rounded-3xl p-7 md:p-8 shadow-xl shadow-black/30 ${className ?? ''}`}>
    {children}
  </div>
);
