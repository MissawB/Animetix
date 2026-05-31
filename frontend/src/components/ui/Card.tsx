import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { fadeUpVariants } from './animations';

import { DynamicAuraWrapper } from '../shared/DynamicAuraWrapper';

interface CardProps {
  children: ReactNode;
  className?: string;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  animate?: boolean;
  hasAura?: boolean;
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  padding = 'lg',
  animate = true,
  hasAura = false
}) => {
  const paddings = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8 md:p-10',
  };

  let content = (
    <div className={`bg-surface-card rounded-token-card shadow-token-card border-token-card border-surface-text/[var(--opacity-card-border)] ${paddings[padding]} ${className}`}>
      {children}
    </div>
  );

  if (hasAura) {
    content = <DynamicAuraWrapper>{content}</DynamicAuraWrapper>;
  }

  if (!animate) return content;

  return (
    <motion.div
      variants={fadeUpVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      {content}
    </motion.div>
  );
};
