# Design: Particle Background and Floating Animation for ForgeHubPage

## Overview
- Goal: Enhance `ForgeHubPage` with a particle background and floating `RelicItem` cards to improve visual polish.
- Approach: Use `framer-motion` for animations as it is already a dependency and is well-suited for React animations.

## Technical Details

### 1. Particle Background
- Location: Within the `min-h-screen` container in `ForgeHubPage.tsx`.
- Implementation: Use `motion.div` for particles, with random initial positions and keyframe animations for floating upwards and fading out.
- Performance: Ensure it is a fixed, pointer-events-none layer to avoid interference.

### 2. Floating Animation
- Location: Wrap `RelicItem` components in `ForgeHubPage.tsx`.
- Implementation: Use `motion.div` with the `animate` prop: `{ y: [0, -10, 0] }`.

## Trade-offs
- Using `framer-motion` for particle animations (instead of pure CSS keyframes) might have a slight performance overhead, but given the simplicity (20 particles), it should be acceptable and provides easier React integration for random initial positions.
- Using `useEffect` to avoid SSR `window` reference errors is necessary.

## Success Criteria
- Particle background exists and animates.
- `RelicItem`s float gently.
- No UI regressions.
