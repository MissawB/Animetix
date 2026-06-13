import React from 'react';
import { motion } from 'framer-motion';

export const GlitchText: React.FC<{children: React.ReactNode, className?: string}> = ({children, className}) => (
  <motion.div
    whileHover={{ x: [-1, 1, -1], transition: { repeat: Infinity, duration: 0.1 } }}
    className={className}
  >
    {children}
  </motion.div>
);
