import { motion } from 'framer-motion';
import { usePersonalizationStore } from '../../store/personalizationStore';

export const DynamicAuraWrapper = ({ children }: { children: React.ReactNode }) => {
  const config = usePersonalizationStore((state) => state.config);
  const isEnabled = usePersonalizationStore((state) => state.isPersonalizationEnabled);
  
  if (!isEnabled || !config || config.aura_type === 'none') return <>{children}</>;

  const getAuraAnimation = () => {
    const intensity = config.aura_intensity || 1;
    const color = config.primary_accent;

    switch (config.aura_type) {
      case 'fire':
        return {
          boxShadow: [
            `0 0 ${15 * intensity}px ${color}`,
            `0 -5px ${25 * intensity}px ${color}`,
            `0 0 ${15 * intensity}px ${color}`,
          ],
          scale: [1, 1.01, 1],
        };
      case 'electric':
        return {
          boxShadow: [
            `0 0 ${10 * intensity}px ${color}`,
            `0 0 ${20 * intensity}px #fff`,
            `0 0 ${10 * intensity}px ${color}`,
          ],
          opacity: [1, 0.8, 1],
        };
      case 'shadow':
        return {
          boxShadow: [
            `0 0 ${20 * intensity}px rgba(0,0,0,0.5)`,
            `0 0 ${40 * intensity}px rgba(0,0,0,0.8)`,
            `0 0 ${20 * intensity}px rgba(0,0,0,0.5)`,
          ],
          filter: ['brightness(1)', 'brightness(0.8)', 'brightness(1)'],
        };
      case 'sparkles':
        return {
          boxShadow: [
            `0 0 ${10 * intensity}px ${color}`,
            `0 0 ${15 * intensity}px #fff`,
            `0 0 ${10 * intensity}px ${color}`,
          ],
        };
      default:
        return {
          boxShadow: [
            `0 0 ${10 * intensity}px ${color}`,
            `0 0 ${20 * intensity}px ${color}`,
            `0 0 ${10 * intensity}px ${color}`,
          ]
        };
    }
  };

  return (
    <motion.div
      animate={getAuraAnimation()}
      transition={{ 
        duration: config.aura_type === 'electric' ? 0.2 : 2, 
        repeat: Infinity,
        repeatType: "mirror"
      }}
      style={{ borderRadius: 'inherit' }}
    >
      {children}
    </motion.div>
  );
};
