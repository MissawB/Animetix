import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { CharacterGrid } from '../CharacterGrid';

const characters = [
  { id: '126071', name: 'Tanjirou Kamado', image: 'https://img/t.png' },
  { id: '127518', name: 'Nezuko Kamado', image: null },
];

it('renders one clickable card per character linking to the character page', () => {
  render(
    <MemoryRouter>
      <CharacterGrid characters={characters} />
    </MemoryRouter>,
  );
  expect(screen.getByRole('link', { name: /tanjirou kamado/i })).toHaveAttribute(
    'href',
    '/media/Character/126071/',
  );
  expect(screen.getByRole('link', { name: /nezuko kamado/i })).toHaveAttribute(
    'href',
    '/media/Character/127518/',
  );
});

it('shows the character image when present', () => {
  render(
    <MemoryRouter>
      <CharacterGrid characters={characters} />
    </MemoryRouter>,
  );
  expect(screen.getByAltText('Tanjirou Kamado')).toHaveAttribute('src', 'https://img/t.png');
});
