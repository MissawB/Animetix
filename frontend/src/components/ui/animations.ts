import { Variants } from 'framer-motion';

/**
 * Animation Design Tokens
 * Centralise les durées et les courbes de bézier pour une cohérence totale.
 */
export const animationTokens = {
  duration: {
    fast: 0.2,
    normal: 0.4,
    slow: 0.6,
  },
  easing: {
    base: [0.4, 0, 0.2, 1] as [number, number, number, number], // standard ease
    spring: [0.175, 0.885, 0.32, 1.275] as [number, number, number, number], // easeOutBack (rebond doux)
    gentle: [0, 0, 0.2, 1] as [number, number, number, number],
  },
};

export const fadeUpVariants: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: { 
      duration: animationTokens.duration.normal,
      ease: animationTokens.easing.base 
    }
  },
  exit: { 
    opacity: 0, 
    y: -20,
    transition: { 
      duration: animationTokens.duration.fast 
    }
  },
};

export const pageVariants: Variants = {
  initial: { opacity: 0, x: -10 },
  animate: { 
    opacity: 1, 
    x: 0,
    transition: { 
      duration: animationTokens.duration.normal,
      ease: animationTokens.easing.gentle
    }
  },
  exit: { 
    opacity: 0, 
    x: 10,
    transition: { 
      duration: animationTokens.duration.fast 
    }
  },
};

export const staggerContainer: Variants = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};
