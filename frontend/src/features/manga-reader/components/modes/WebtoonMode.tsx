import React, { useState, useEffect, useRef } from 'react';
import { useReaderStore, ImageWidth, GapSize } from '../../stores/useReaderStore';

export const WebtoonMode = () => {
  const { pages, gapSize, imageWidth, setPageDimensions } = useReaderStore();
  const [visibleCount, setVisibleCount] = useState(() => Math.min(pages.length, 3));

  const sentinelRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Record<number, HTMLDivElement | null>>({});

  // Reset visibility count when the page list changes. Adjusting state during render
  // (React's "storing previous value" pattern) avoids the cascading-render that an
  // effect-based setState would cause.
  const [prevPages, setPrevPages] = useState(pages);
  if (prevPages !== pages) {
    setPrevPages(pages);
    setVisibleCount(Math.min(pages.length, 3));
  }

  // Infinite Scroll Sentinel Observer
  useEffect(() => {
    if (pages.length === 0 || visibleCount >= pages.length) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setVisibleCount((prev) => Math.min(pages.length, prev + 3));
        }
      },
      { rootMargin: '600px' } // Pre-trigger loading 600px before reaching the end
    );

    const currentSentinel = sentinelRef.current;
    if (currentSentinel) {
      observer.observe(currentSentinel);
    }

    return () => {
      if (currentSentinel) {
        observer.unobserve(currentSentinel);
      }
    };
  }, [visibleCount, pages.length]);

  // Synchronize currentPageIndex with scrolling position
  useEffect(() => {
    if (pages.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const indexAttr = entry.target.getAttribute('data-index');
            if (indexAttr !== null) {
              const pageIndex = parseInt(indexAttr, 10);
              if (!isNaN(pageIndex)) {
                useReaderStore.getState().setCurrentPageIndex(pageIndex);
              }
            }
          }
        });
      },
      {
        rootMargin: '-25% 0px -50% 0px', // Focus window in the upper/middle viewport area
        threshold: 0.1,
      }
    );

    const observedElements: HTMLDivElement[] = [];
    for (let i = 0; i < visibleCount; i++) {
      const el = pageRefs.current[i];
      if (el) {
        observer.observe(el);
        observedElements.push(el);
      }
    }

    return () => {
      observedElements.forEach((el) => observer.unobserve(el));
    };
  }, [visibleCount, pages.length]);

  if (pages.length === 0) {
    return <div className="flex items-center justify-center h-64 text-gray-500 italic">Aucune page chargée</div>;
  }

  // Sizing and spacing classes helper functions
  const getGapClass = (size: GapSize) => {
    switch (size) {
      case 'none': return 'gap-0';
      case 'small': return 'gap-4';
      case 'medium': return 'gap-8';
      default: return 'gap-0';
    }
  };

  const getMaxWidthClass = (width: ImageWidth) => {
    switch (width) {
      case 'scale-80': return 'max-w-lg';
      case 'scale-100': return 'max-w-2xl';
      case 'scale-xl': return 'max-w-3xl';
      case 'scale-2xl': return 'max-w-4xl';
      case 'scale-full': return 'max-w-full w-full';
      default: return 'max-w-2xl';
    }
  };

  const visiblePages = pages.slice(0, visibleCount);

  return (
    <div className={`flex flex-col items-center ${getGapClass(gapSize)} w-full mx-auto pb-32`}>
      {visiblePages.map((page, index) => (
        <div
          key={page.index}
          ref={(el) => { pageRefs.current[index] = el; }}
          data-index={page.index}
          className={`w-full flex justify-center transition-all duration-300 ${getMaxWidthClass(imageWidth)}`}
        >
          <img
            src={page.url}
            alt={`Page ${page.index + 1}`}
            className="w-full h-auto block rounded-lg shadow-md border border-white/5"
            onLoad={(e) => setPageDimensions(page.url, e.currentTarget.naturalWidth, e.currentTarget.naturalHeight)}
            loading="lazy"
            decoding="async"
          />
        </div>
      ))}
      
      {/* Scroll Sentinel */}
      {visibleCount < pages.length && (
        <div
          ref={sentinelRef}
          className="h-20 w-full flex items-center justify-center text-gray-500 text-xs italic tracking-wider uppercase font-bold"
        >
          Chargement des pages suivantes...
        </div>
      )}
    </div>
  );
};

