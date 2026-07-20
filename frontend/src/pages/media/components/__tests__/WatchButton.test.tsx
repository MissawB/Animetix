import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { WatchButton } from '../WatchButton';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) =>
      typeof defaultValue === 'string' ? defaultValue : key,
  }),
}));

it('links to a JustWatch search when no platform data exists', () => {
  render(<WatchButton title="Kimetsu no Yaiba" platforms={[]} />);
  const link = screen.getByRole('link', { name: /où regarder/i });
  expect(link).toHaveAttribute(
    'href',
    'https://www.justwatch.com/fr/recherche?q=Kimetsu%20no%20Yaiba',
  );
  expect(link).toHaveAttribute('target', '_blank');
});

it('opens a panel listing platforms when data exists', () => {
  render(
    <WatchButton
      title="Show"
      platforms={[
        { platform: 'Crunchyroll', has_vf: true, has_vostfr: true, status: 'Abonnement' },
      ]}
    />,
  );
  expect(screen.queryByText('Crunchyroll')).toBeNull();
  fireEvent.click(screen.getByRole('button', { name: /où regarder/i }));
  expect(screen.getByText('Crunchyroll')).toBeInTheDocument();
  expect(screen.getByText('VF')).toBeInTheDocument();
  expect(screen.getByText('VOSTFR')).toBeInTheDocument();
});

it('closes the panel on Escape', () => {
  render(<WatchButton title="Show" platforms={[{ platform: 'ADN', has_vf: true }]} />);
  fireEvent.click(screen.getByRole('button', { name: /où regarder/i }));
  expect(screen.getByText('ADN')).toBeInTheDocument();
  fireEvent.keyDown(document, { key: 'Escape' });
  expect(screen.queryByText('ADN')).toBeNull();
});
