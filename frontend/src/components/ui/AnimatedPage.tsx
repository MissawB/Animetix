import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { pageVariants } from './animations';

interface AnimatedPageProps {
  children: ReactNode;
}

/**
 * Wrapper de page pour gérer les transitions fluides entre les routes.
 * Utilise les tokens d'animation pour une cohérence globale.
 */
export const AnimatedPage: React.FC<AnimatedPageProps> = ({ children }) => {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className="w-full h-full"
    >
      {children}
    </motion.div>
  );
};
