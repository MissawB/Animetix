import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { HeroBanner } from '../HeroBanner';

const renderHero = (hero: Parameters<typeof HeroBanner>[0]['hero']) =>
  render(
    <MemoryRouter>
      <HeroBanner hero={hero} mediaType="Anime" />
    </MemoryRouter>,
  );

it('renders the hero title, rating, year and CTA', () => {
  renderHero({
    id: '1',
    title: 'Cowboy Bebop',
    media_type: 'Anime',
    rating: 9.1,
    year: 1998,
    genres: ['Action'],
  });
  expect(screen.getByText('Cowboy Bebop')).toBeInTheDocument();
  expect(screen.getByText('9.1')).toBeInTheDocument();
  expect(screen.getByText('1998')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /voir la fiche/i })).toHaveAttribute(
    'href',
    '/media/anime/1/',
  );
});
