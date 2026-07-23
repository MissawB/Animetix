import React from 'react';
import { motion } from 'framer-motion';

interface CyberButtonProps {
  onClick: () => void;
  children: React.ReactNode;
  className?: string;
}

/** Le marteau de la Forge : bouton braise (or -> fer chaud) au halo qui
 *  respire. Nom historique conservé pour ne pas toucher les appelants. */
export const CyberButton: React.FC<CyberButtonProps> = ({ onClick, children, className }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.96 }}
      animate={{
        boxShadow: [
          '0 0 18px rgba(253, 185, 19, 0.25)',
          '0 0 34px rgba(232, 68, 43, 0.4)',
          '0 0 18px rgba(253, 185, 19, 0.25)',
        ],
      }}
      transition={{
        boxShadow: {
          repeat: Infinity,
          duration: 2,
          ease: 'easeInOut',
        },
      }}
      onClick={onClick}
      className={`font-manga cursor-pointer border-none bg-gradient-to-br from-[#FDB913] to-[#E8442B] uppercase tracking-wide text-[#0B0C10] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#FDB913] ${className ?? ''}`}
    >
      {children}
    </motion.button>
  );
};
