import React from 'react';
import { useReaderStore, ImageWidth } from '../../stores/useReaderStore';
import { ChevronLeft, ChevronRight } from 'lucide-react';

export const TraditionalMode = () => {
  const {
    pages,
    currentPageIndex,
    readingDirection,
    pageLayout,
    splitWidePages,
    imageWidth,
    pageDimensions,
    panningStep,
    setPageDimensions,
    goToNextPage,
    goToPrevPage
  } = useReaderStore();

  if (pages.length === 0) {
    return <div className="flex items-center justify-center h-64 text-gray-500 italic">Aucune page chargée</div>;
  }

  const currentPage = pages[currentPageIndex];
  const isRtl = readingDirection === 'rtl';

  // Sizing helper
  const getMaxWidthClass = (width: ImageWidth, isDouble: boolean) => {
    if (isDouble) {
      switch (width) {
        case 'scale-80': return 'max-w-4xl';
        case 'scale-100': return 'max-w-5xl';
        case 'scale-xl': return 'max-w-6xl';
        case 'scale-2xl': return 'max-w-7xl';
        case 'scale-full': return 'max-w-full w-full';
        default: return 'max-w-6xl';
      }
    } else {
      switch (width) {
        case 'scale-80': return 'max-w-lg';
        case 'scale-100': return 'max-w-2xl';
        case 'scale-xl': return 'max-w-3xl';
        case 'scale-2xl': return 'max-w-4xl';
        case 'scale-full': return 'max-w-full w-full';
        default: return 'max-w-3xl';
      }
    }
  };

  // Determine if current page is wide
  const isCurrentWide = pageDimensions[currentPage?.url]?.isWide ?? false;

  // Determine if we can and should show double pages
  const nextPageIndex = currentPageIndex + 1;
  const hasNextPage = nextPageIndex < pages.length;
  const nextPage = hasNextPage ? pages[nextPageIndex] : null;
  const isNextWide = nextPage ? (pageDimensions[nextPage.url]?.isWide ?? false) : false;

  const isDoubleActive =
    pageLayout === 'double' &&
    hasNextPage &&
    !isCurrentWide &&
    !isNextWide;

  // Preloading index calculation (previous 1 page, next 3 pages)
  const preloadIndices = [
    currentPageIndex - 1,
    currentPageIndex + 1,
    currentPageIndex + 2,
    currentPageIndex + 3
  ].filter(idx => idx >= 0 && idx < pages.length);

  return (
    <div className="flex flex-col items-center w-full px-4 select-none">
      {/* Hidden Preloader Container */}
      <div className="hidden" aria-hidden="true" style={{ width: 0, height: 0, overflow: 'hidden', position: 'absolute' }}>
        {preloadIndices.map((idx) => {
          const pg = pages[idx];
          return (
            <img
              key={pg.url}
              src={pg.url}
              alt=""
              onLoad={(e) => setPageDimensions(pg.url, e.currentTarget.naturalWidth, e.currentTarget.naturalHeight)}
              loading="lazy"
              decoding="async"
            />
          );
        })}
      </div>

      <div className={`relative group w-full flex justify-center items-center ${getMaxWidthClass(imageWidth, isDoubleActive)}`}>
        {/* Navigation Overlays */}
        {/* Left Click Area */}
        <button
          onClick={isRtl ? goToNextPage : goToPrevPage}
          className="absolute left-0 top-0 bottom-0 w-1/5 flex items-center justify-start pl-4 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-r from-black/50 to-transparent cursor-pointer z-20 rounded-l-2xl border-none outline-none focus:opacity-100"
          title={isRtl ? "Page suivante" : "Page précédente"}
        >
          <ChevronLeft className="w-12 h-12 text-white filter drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]" />
        </button>

        {/* Right Click Area */}
        <button
          onClick={isRtl ? goToPrevPage : goToNextPage}
          className="absolute right-0 top-0 bottom-0 w-1/5 flex items-center justify-end pr-4 opacity-0 group-hover:opacity-100 transition-opacity bg-gradient-to-l from-black/50 to-transparent cursor-pointer z-20 rounded-r-2xl border-none outline-none focus:opacity-100"
          title={isRtl ? "Page précédente" : "Page suivante"}
        >
          <ChevronRight className="w-12 h-12 text-white filter drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]" />
        </button>

        {/* Reader Display Area */}
        {isDoubleActive && nextPage ? (
          /* Double Page Layout side-by-side */
          <div className="flex justify-center items-stretch gap-4 w-full animate-fade-in">
            {isRtl ? (
              <>
                {/* RTL order: Page B (next) on Left, Page A (current) on Right */}
                <div className="w-1/2 flex justify-end">
                  <img
                    src={nextPage.url}
                    alt={`Page ${nextPage.index + 1}`}
                    onLoad={(e) => setPageDimensions(nextPage.url, e.currentTarget.naturalWidth, e.currentTarget.naturalHeight)}
                    className="max-h-[80vh] w-auto object-contain rounded-xl shadow-2xl border border-white/10 hover:border-white/20 transition-colors"
                    loading="lazy"
                    decoding="async"
                  />
                </div>
                <div className="w-1/2 flex justify-start">
                  <img
                    src={currentPage.url}
                    alt={`Page ${currentPage.index + 1}`}
                    onLoad={(e) => setPageDimensions(currentPage.url, e.currentTarget.naturalWidth, e.currentTarget.naturalHeight)}
                    className="max-h-[80vh] w-auto object-contain rounded-xl shadow-2xl border border-white/10 hover:border-white/20 transition-colors"
                    loading="lazy"
                    decoding="async"
                  />
                </div>
              </>
            ) : (
              <>
                {/* LTR order: Page A (current) on Left, Page B (next) on Right */}
                <div className="w-1/2 flex justify-end">
                  <img
                    src={currentPage.url}
                    alt={`Page ${currentPage.index + 1}`}
                    onLoad={(e) => setPageDimensions(currentPage.url, e.currentTarget.naturalWidth, e.currentTarget.naturalHeight)}
                    className="max-h-[80vh] w-auto object-contain rounded-xl shadow-2xl border border-white/10 hover:border-white/20 transition-colors"
                    loading="lazy"
                    decoding="async"
                  />
                </div>
                <div className="w-1/2 flex justify-start">
                  <img
                    src={nextPage.url}
                    alt={`Page ${nextPage.index + 1}`}
                    onLoad={(e) => setPageDimensions(nextPage.url, e.currentTarget.naturalWidth, e.currentTarget.naturalHeight)}
                    className="max-h-[80vh] w-auto object-contain rounded-xl shadow-2xl border border-white/10 hover:border-white/20 transition-colors"
                    loading="lazy"
                    decoding="async"
                  />
                </div>
              </>
            )}
          </div>
        ) : splitWidePages && isCurrentWide ? (
          /* Split Wide Page Layout */
          (() => {
            const dims = pageDimensions[currentPage.url];
            const pageAspect = dims ? dims.width / dims.height : 1.4;
            const containerAspect = pageAspect / 2;

            const transformStyle = {
              width: '200%',
              height: '100%',
              transform: isRtl
                ? (panningStep === 0 ? 'translateX(-50%)' : 'translateX(0%)')
                : (panningStep === 0 ? 'translateX(0%)' : 'translateX(-50%)'),
              transition: 'transform 0.35s cubic-bezier(0.25, 1, 0.5, 1)',
            };

            return (
              <div
                className="w-full overflow-hidden relative rounded-xl shadow-2xl border border-white/10"
                style={{ aspectRatio: containerAspect }}
              >
                <img
                  src={currentPage.url}
                  alt={`Page ${currentPage.index + 1} - Partie ${panningStep + 1}`}
                  onLoad={(e) => setPageDimensions(currentPage.url, e.currentTarget.naturalWidth, e.currentTarget.naturalHeight)}
                  className="max-w-none h-full object-cover absolute top-0 left-0"
                  style={transformStyle}
                  loading="lazy"
                  decoding="async"
                />
              </div>
            );
          })()
        ) : (
          /* Standard Single Page Layout */
          <div className="w-full flex justify-center">
            <img
              src={currentPage.url}
              alt={`Page ${currentPage.index + 1}`}
              onLoad={(e) => setPageDimensions(currentPage.url, e.currentTarget.naturalWidth, e.currentTarget.naturalHeight)}
              className="w-full h-auto max-h-[85vh] object-contain rounded-xl shadow-2xl border border-white/10"
              loading="lazy"
              decoding="async"
            />
          </div>
        )}
      </div>

      {/* Info and Progress Pill */}
      <div className="mt-8 flex items-center gap-4 text-xs font-bold text-gray-400 bg-navy-900/40 backdrop-blur-md px-6 py-2.5 rounded-full border border-white/5">
        <span className="uppercase tracking-widest text-[10px]">
          {isDoubleActive && nextPage ? (
            <>Pages {currentPage.index + 1} - {nextPage.index + 1} sur {pages.length}</>
          ) : splitWidePages && isCurrentWide ? (
            <>Page {currentPage.index + 1} (Partie {panningStep + 1}/2) sur {pages.length}</>
          ) : (
            <>Page {currentPageIndex + 1} sur {pages.length}</>
          )}
        </span>
        {isDoubleActive && (
          <span className="bg-anime-accent/20 text-anime-accent px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-black">
            Double Page
          </span>
        )}
        {splitWidePages && isCurrentWide && (
          <span className="bg-anime-accent/20 text-anime-accent px-2 py-0.5 rounded text-[8px] uppercase tracking-wider font-black">
            Double Découpée
          </span>
        )}
      </div>
    </div>
  );
};

