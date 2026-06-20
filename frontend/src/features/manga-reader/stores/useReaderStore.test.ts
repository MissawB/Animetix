import { useReaderStore } from './useReaderStore';
import { act } from '@testing-library/react';
import { renderHook } from '@testing-library/react';
import { describe, it, expect, beforeEach } from 'vitest';

describe('useReaderStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    act(() => {
      const store = useReaderStore.getState();
      store.setMode('traditional');
      store.setPages([]);
      store.setCurrentPageIndex(0);
      store.setReadingDirection('rtl');
      store.setPageLayout('single');
      store.setSplitWidePages(true);
      store.setImageWidth('scale-xl');
      store.setGapSize('none');
      store.setBrightness(100);
      
      // Clear internal page dimensions and panning steps
      useReaderStore.setState({ pageDimensions: {}, panningStep: 0 });
    });
  });

  it('should switch reader mode', () => {
    const { result } = renderHook(() => useReaderStore());
    act(() => result.current.setMode('webtoon'));
    expect(result.current.mode).toBe('webtoon');
  });

  it('should apply and respect brightness bounds', () => {
    const { result } = renderHook(() => useReaderStore());
    
    // Set valid brightness
    act(() => result.current.setBrightness(75));
    expect(result.current.brightness).toBe(75);

    // Clamp to minimum boundary (20)
    act(() => result.current.setBrightness(10));
    expect(result.current.brightness).toBe(20);

    // Clamp to maximum boundary (100)
    act(() => result.current.setBrightness(150));
    expect(result.current.brightness).toBe(100);
  });

  describe('Navigation Logic', () => {
    const testPages = [
      { url: 'page1.jpg', index: 0 },
      { url: 'page2.jpg', index: 1 },
      { url: 'page3.jpg', index: 2 },
      { url: 'page4.jpg', index: 3 },
      { url: 'page5.jpg', index: 4 },
    ];

    beforeEach(() => {
      act(() => {
        useReaderStore.getState().setPages(testPages);
      });
    });

    it('should navigate step-by-step in single page layout', () => {
      const { result } = renderHook(() => useReaderStore());
      
      expect(result.current.currentPageIndex).toBe(0);

      // Next
      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(1);

      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(2);

      // Previous
      act(() => result.current.goToPrevPage());
      expect(result.current.currentPageIndex).toBe(1);
    });

    it('should navigate by 2 pages in double page layout when pages are not wide', () => {
      const { result } = renderHook(() => useReaderStore());
      
      act(() => result.current.setPageLayout('double'));
      expect(result.current.currentPageIndex).toBe(0);

      // Page 1 and Page 2 are normal (not wide), so double page forms. Next should jump to Page 3 (index 2).
      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(2);

      // Page 3 and Page 4 are normal, next jumps to Page 5 (index 4).
      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(4);

      // Prev should jump back by 2 pages
      act(() => result.current.goToPrevPage());
      expect(result.current.currentPageIndex).toBe(2);

      act(() => result.current.goToPrevPage());
      expect(result.current.currentPageIndex).toBe(0);
    });

    it('should split wide pages and navigate through panning steps', () => {
      const { result } = renderHook(() => useReaderStore());
      
      // Mark Page 2 (index 1) as wide
      act(() => {
        result.current.setPageDimensions('page2.jpg', 2000, 1000); // aspect ratio = 2.0 > 1.2
      });

      expect(result.current.currentPageIndex).toBe(0);

      // Go to Page 2
      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(1);
      expect(result.current.panningStep).toBe(0);

      // Next step on wide page should increment panning step, not page index
      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(1);
      expect(result.current.panningStep).toBe(1);

      // Next step should then proceed to Page 3
      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(2);
      expect(result.current.panningStep).toBe(0);

      // Going back should land on wide Page 2 at panningStep 1 (second half)
      act(() => result.current.goToPrevPage());
      expect(result.current.currentPageIndex).toBe(1);
      expect(result.current.panningStep).toBe(1);

      // Prev step on wide page should decrement panning step
      act(() => result.current.goToPrevPage());
      expect(result.current.currentPageIndex).toBe(1);
      expect(result.current.panningStep).toBe(0);

      // Prev step should then go to Page 1
      act(() => result.current.goToPrevPage());
      expect(result.current.currentPageIndex).toBe(0);
      expect(result.current.panningStep).toBe(0);
    });

    it('should fall back to single page navigation if double page contains a wide page', () => {
      const { result } = renderHook(() => useReaderStore());
      
      act(() => result.current.setPageLayout('double'));
      
      // Mark Page 2 (index 1) as wide
      act(() => {
        result.current.setPageDimensions('page2.jpg', 2000, 1000);
      });

      expect(result.current.currentPageIndex).toBe(0);

      // Page 1 is normal, but Page 2 is wide. So they cannot be paired side-by-side.
      // Next should only go to Page 2 (index 1), not Page 3 (index 2).
      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(1);
      expect(result.current.panningStep).toBe(0);

      // Page 2 is wide, next goes to panning step 1
      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(1);
      expect(result.current.panningStep).toBe(1);

      // Next goes to Page 3 (index 2)
      act(() => result.current.goToNextPage());
      expect(result.current.currentPageIndex).toBe(2);
      expect(result.current.panningStep).toBe(0);
    });
  });
});

