import React from 'react';
import { motion } from 'framer-motion';

interface CyberButtonProps {
  onClick: () => void;
  children: React.ReactNode;
  className?: string;
}

export const CyberButton: React.FC<CyberButtonProps> = ({ onClick, children, className }) => {
  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      animate={{
        boxShadow: [
          '0 0 10px rgba(0, 243, 255, 0.5)',
          '0 0 20px rgba(0, 243, 255, 0.8)',
          '0 0 10px rgba(0, 243, 255, 0.5)',
        ],
      }}
      transition={{
        boxShadow: {
          repeat: Infinity,
          duration: 1.5,
          ease: 'easeInOut',
        },
      }}
      onClick={onClick}
      className={`px-6 py-2 bg-cyberpunk-panel border border-cyberpunk-neonCyan text-cyberpunk-neonCyan font-mono rounded uppercase tracking-widest ${className}`}
    >
      {children}
    </motion.button>
  );
};
