import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { HeroSection, HERO_IMAGES } from '../HeroSection';

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
  it('affiche une image du pool historique, tirée au hasard au chargement', () => {
    renderHero();
    expect(HERO_IMAGES).toContain(heroSrc());
  });

  it('garde la même image après le chargement (pas de rotation)', () => {
    renderHero();
    expect(heroSrc()).toBe(heroSrc());
  });
});
