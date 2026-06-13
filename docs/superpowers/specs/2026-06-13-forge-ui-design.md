# Design Specification: Forge UI - Cyberpunk Immersive

## 1. Overview
The goal is to transform the existing `/static/forge/` page into a high-contrast, immersive Cyberpunk terminal interface. The redesign focuses on aesthetic enhancements, improved dark mode usability, and dynamic interaction feedback.

## 2. Design Direction
**Selected Style:** "Full Cyberpunk Immersive"
- **Palette:** Deep black background, vibrant neon cyan (active state), magenta (alerts/chaos), pure white (text).
- **Aesthetic:** Terminal-like interface with glassmorphism, subtle scanlines, and glitch effects.

## 3. UI Components
- **Fusion Panels:** Glassmorphism-based panels (`backdrop-filter: blur(10px)`) with active-state animated borders.
- **Sliders (Chaos/Balance):** Customized range inputs with neon glowing tracks and stylized handles.
- **Button ("Forger"):** Central element with dynamic glow, pulsating animation, and scanline sweep effect.
- **Typography:** Implementation of `font-mono` for all technical data fields.

## 4. Interaction & Feedback
- **Glitch Effects:** Micro-glitches (Framer Motion) on the main title during interaction.
- **Dynamic Counters:** Numerical counters for slider values.
- **Loading State:** Updated with a scanning progress animation.

## 5. Observability & Validation
- **VRT:** Use Playwright for visual regression testing (snapshots) on core UI states.
- **Monitoring:** Ensure all interactions are captured by PostHog for UX analysis.
