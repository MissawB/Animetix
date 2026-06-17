import { render, screen } from '@testing-library/react';
import { MangaReader } from './MangaReader';
import { describe, it, expect, vi } from 'vitest';

vi.mock('../stores/useReaderStore', () => ({
  useReaderStore: () => ({
    mode: 'webtoon',
    setMode: vi.fn(),
  }),
}));

describe('MangaReader', () => {
  it('renders correctly', () => {
    render(<MangaReader />);
    expect(screen.getByText('webtoon')).toBeDefined();
    expect(screen.getByText('traditional')).toBeDefined();
    expect(screen.getByText('interactive')).toBeDefined();
  });
});
