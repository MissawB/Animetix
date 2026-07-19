import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { DetailHero } from '../DetailHero';
import type { MediaDetail } from '../../../../types';

const mockItem: MediaDetail = {
  id: '123',
  title: 'Demon Slayer',
  media_type: 'Anime',
  image: 'https://example.com/poster.jpg',
  title_english: 'Kimetsu no Yaiba',
  year: '2019',
  popularity: 3,
  genres: ['Action', 'Shounen'],
  description: 'A tale of demons and heroes',
};

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};

it('renders the media title as a heading', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Anime" itemId="123" />);
  expect(screen.getByRole('heading', { level: 1, name: /demon slayer/i })).toBeInTheDocument();
});

it('renders the english title', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Anime" itemId="123" />);
  expect(screen.getByText(/kimetsu no yaiba/i)).toBeInTheDocument();
});

it('renders genre badges', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Anime" itemId="123" />);
  expect(screen.getByText('Action')).toBeInTheDocument();
  expect(screen.getByText('Shounen')).toBeInTheDocument();
});

it('renders release year', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Anime" itemId="123" />);
  expect(screen.getByText('2019')).toBeInTheDocument();
});

it('renders popularity as a single string with hash', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Anime" itemId="123" />);
  // This ensures #3 is rendered as one text node, not split across elements
  const text = screen.getByText('#3');
  expect(text).toBeInTheDocument();
});

it('renders N/A for missing popularity', () => {
  const itemWithoutPopularity = { ...mockItem, popularity: undefined };
  renderWithRouter(<DetailHero item={itemWithoutPopularity} mediaType="Anime" itemId="123" />);
  expect(screen.getByText('#N/A')).toBeInTheDocument();
});

it('renders hero background image', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Anime" itemId="123" />);
  const bgImage = screen.getByRole('img', { hidden: true });
  expect(bgImage).toHaveAttribute('src', mockItem.image);
});

it('renders LIRE LE MANGA button for manga type with correct link', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Manga" itemId="456" />);
  const link = screen.getByRole('link', { name: /lire le manga/i });
  expect(link).toHaveAttribute('href', '/media/manga/456/1/');
});

it('renders VOIR button for anime type', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Anime" itemId="123" />);
  expect(screen.getByRole('button', { name: /voir/i })).toBeInTheDocument();
});

it('renders action buttons as decorative (no handlers)', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Anime" itemId="123" />);
  const addButton = screen.getByRole('button', { name: /ajouter/i });
  expect(addButton).toBeInTheDocument();
  const favorisButton = screen.getByRole('button', { name: /favoris/i });
  expect(favorisButton).toBeInTheDocument();
});

it('renders share button', () => {
  renderWithRouter(<DetailHero item={mockItem} mediaType="Anime" itemId="123" />);
  const shareButton = screen.getByRole('button', { name: /partager/i });
  expect(shareButton).toBeInTheDocument();
});
