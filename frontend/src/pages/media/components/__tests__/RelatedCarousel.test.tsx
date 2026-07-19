import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { RelatedCarousel } from '../RelatedCarousel';

const items = [
  { id: '10', title: 'Saison 2', image: '' },
  { id: '11', title: 'Film', image: '' },
];

it('renders a capitalized detail link per item', () => {
  render(
    <MemoryRouter>
      <RelatedCarousel items={items} mediaType="Anime" />
    </MemoryRouter>,
  );
  expect(screen.getByRole('link', { name: /saison 2/i })).toHaveAttribute(
    'href',
    '/media/Anime/10/',
  );
  expect(screen.getByRole('link', { name: /film/i })).toHaveAttribute('href', '/media/Anime/11/');
});
