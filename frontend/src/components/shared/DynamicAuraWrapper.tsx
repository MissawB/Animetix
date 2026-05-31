import { motion } from 'framer-motion';
import { usePersonalizationStore } from '../../store/personalizationStore';

export const DynamicAuraWrapper = ({ children }: { children: React.ReactNode }) => {
  const config = usePersonalizationStore((state) => state.config);
  
  if (!config || config.aura_type === 'none') return <>{children}</>;

  return (
    <motion.div
      animate={{
        boxShadow: [
          `0 0 ${10 * config.aura_intensity}px ${config.primary_accent}`,
          `0 0 ${20 * config.aura_intensity}px ${config.primary_accent}`,
          `0 0 ${10 * config.aura_intensity}px ${config.primary_accent}`,
        ]
      }}
      transition={{ duration: 2, repeat: Infinity }}
      style={{ borderRadius: 'inherit' }}
    >
      {children}
    </motion.div>
  );
};
