import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { InteractiveMode } from '../InteractiveMode';
import { useReaderStore } from '../../../stores/useReaderStore';
import type { MangaPage } from '../../../stores/useReaderStore';

vi.mock('../../../stores/useReaderStore');

interface StoreShape {
  pages: MangaPage[];
  currentPageIndex: number;
}

const mockStore = (state: StoreShape) => {
  vi.mocked(useReaderStore).mockReturnValue(
    state as unknown as ReturnType<typeof useReaderStore>,
  );
};

describe('InteractiveMode', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders a fallback message when no page is loaded', () => {
    mockStore({ pages: [], currentPageIndex: 0 });
    render(<InteractiveMode />);
    expect(screen.getByText('Aucune page chargée')).toBeInTheDocument();
  });

  it('renders the current page image with alt text and source', () => {
    mockStore({
      pages: [{ url: 'https://cdn/p1.png', index: 0 }],
      currentPageIndex: 0,
    });
    render(<InteractiveMode />);
    const img = screen.getByAltText('Interactive Page 1') as HTMLImageElement;
    expect(img).toBeInTheDocument();
    expect(img.src).toBe('https://cdn/p1.png');
  });

  it('renders the explanatory caption', () => {
    mockStore({
      pages: [{ url: 'https://cdn/p1.png', index: 0 }],
      currentPageIndex: 0,
    });
    render(<InteractiveMode />);
    expect(screen.getByText(/Le mode interactif utilise l'IA/i)).toBeInTheDocument();
  });

  it('uses the page at currentPageIndex', () => {
    mockStore({
      pages: [
        { url: 'https://cdn/p1.png', index: 0 },
        { url: 'https://cdn/p2.png', index: 1 },
      ],
      currentPageIndex: 1,
    });
    render(<InteractiveMode />);
    const img = screen.getByAltText('Interactive Page 2') as HTMLImageElement;
    expect(img.src).toBe('https://cdn/p2.png');
  });
});
