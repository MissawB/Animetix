import { render, screen } from '@testing-library/react';
import { MangaReader } from './MangaReader';
import { describe, it, expect, vi } from 'vitest';

const mockStoreState = {
  mode: 'webtoon',
  pages: [],
  currentPageIndex: 0,
  readingDirection: 'rtl',
  pageLayout: 'single',
  splitWidePages: true,
  imageWidth: 'scale-xl',
  gapSize: 'none',
  brightness: 100,
  setMode: vi.fn(),
  setPages: vi.fn(),
  setCurrentPageIndex: vi.fn(),
  setReadingDirection: vi.fn(),
  setPageLayout: vi.fn(),
  setSplitWidePages: vi.fn(),
  setImageWidth: vi.fn(),
  setGapSize: vi.fn(),
  setBrightness: vi.fn(),
  goToNextPage: vi.fn(),
  goToPrevPage: vi.fn(),
};

vi.mock('../stores/useReaderStore', () => {
  return {
    useReaderStore: Object.assign(() => mockStoreState, {
      getState: () => mockStoreState,
    }),
  };
});

describe('MangaReader', () => {
  it('renders correctly', () => {
    render(<MangaReader />);
    expect(screen.getByText('webtoon')).toBeDefined();
    expect(screen.getByText('traditional')).toBeDefined();
    expect(screen.getByText('interactive')).toBeDefined();
  });
});

