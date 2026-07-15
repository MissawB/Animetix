import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { MediaCard } from '../MediaCard';
import { vi } from 'vitest';

vi.mock('../../../../utils/apiClient', () => ({ apiClient: vi.fn() }));

const base = { id: '1', title: 'Item 1', image: '' };

describe('MediaCard', () => {
  it('shows the fiche link and no fake streaming buttons', () => {
    render(
      <MemoryRouter>
        <MediaCard item={{ ...base, media_type: 'Anime' }} />
      </MemoryRouter>,
    );
    expect(screen.getByRole('link', { name: /fiche/i })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /commencer|play|lire/i })).toBeNull();
  });

  it('shows the favorite button only for Manga', () => {
    const { rerender } = render(
      <MemoryRouter>
        <MediaCard item={{ ...base, media_type: 'Manga' }} />
      </MemoryRouter>,
    );
    expect(screen.getByRole('button', { name: /favori/i })).toBeInTheDocument();

    rerender(
      <MemoryRouter>
        <MediaCard item={{ ...base, media_type: 'Anime' }} />
      </MemoryRouter>,
    );
    expect(screen.queryByRole('button', { name: /favori/i })).toBeNull();
  });
});
