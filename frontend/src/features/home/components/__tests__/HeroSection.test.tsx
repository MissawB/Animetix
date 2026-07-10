import { render, screen, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { HeroSection, HERO_IMAGES, HERO_ROTATION_MS } from '../HeroSection';

vi.mock('../../data/useGameModes', () => ({
  useGameModes: () => ({ isEn: false }),
}));

const renderHero = () =>
  render(
    <MemoryRouter>
      <HeroSection />
    </MemoryRouter>,
  );

const heroSrc = () =>
  (screen.getByAltText('Hero Illustration') as HTMLImageElement).getAttribute('src');

describe('HeroSection', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('démarre sur une image du pool historique', () => {
    renderHero();
    expect(HERO_IMAGES).toContain(heroSrc());
  });

  it("tourne automatiquement à l'intervalle et boucle sur tout le pool", () => {
    renderHero();
    const seen = new Set<string>([heroSrc()!]);

    for (let i = 0; i < HERO_IMAGES.length - 1; i++) {
      const before = heroSrc();
      act(() => {
        vi.advanceTimersByTime(HERO_ROTATION_MS);
      });
      expect(heroSrc()).not.toBe(before); // l'image change à chaque tick
      seen.add(heroSrc()!);
    }

    // Après un cycle complet, toutes les images du pool sont passées.
    expect(seen.size).toBe(HERO_IMAGES.length);
  });

  it("nettoie l'intervalle au démontage", () => {
    const { unmount } = renderHero();
    const clearSpy = vi.spyOn(window, 'clearInterval');
    unmount();
    expect(clearSpy).toHaveBeenCalled();
  });
});
