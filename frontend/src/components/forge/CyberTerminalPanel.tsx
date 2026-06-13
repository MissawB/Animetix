import React from 'react';

export const CyberTerminalPanel: React.FC<{children: React.ReactNode, className?: string}> = ({children, className}) => (
  <div className={`backdrop-blur-md bg-cyberpunk-panel border border-cyberpunk-panelBorder rounded-3xl ${className}`}>
    {children}
  </div>
);
