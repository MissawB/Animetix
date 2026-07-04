import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { installLazyImageRescue } from '../lazyImageRescue';

// Capture les éléments observés + expose un moyen de simuler l'intersection.
let observed: Element[] = [];
let triggerIntersection: (el: Element, isIntersecting: boolean) => void;

class MockIntersectionObserver {
  private cb: IntersectionObserverCallback;
  constructor(cb: IntersectionObserverCallback) {
    this.cb = cb;
    triggerIntersection = (el, isIntersecting) => {
      this.cb(
        [{ target: el, isIntersecting } as unknown as IntersectionObserverEntry],
        this as unknown as IntersectionObserver,
      );
    };
  }
  observe(el: Element) { observed.push(el); }
  unobserve(el: Element) { observed = observed.filter((o) => o !== el); }
  disconnect() { observed = []; }
}

describe('installLazyImageRescue', () => {
  let cleanup: () => void;

  beforeEach(() => {
    observed = [];
    document.body.innerHTML = '';
    vi.stubGlobal('IntersectionObserver', MockIntersectionObserver);
  });

  afterEach(() => {
    cleanup?.();
    vi.unstubAllGlobals();
  });

  it('forces a stuck in-view lazy image to load (eager) on intersection', () => {
    const img = document.createElement('img');
    img.setAttribute('loading', 'lazy');
    img.setAttribute('src', 'poster.jpg');
    document.body.appendChild(img);

    cleanup = installLazyImageRescue();
    expect(observed).toContain(img);

    triggerIntersection(img, true);
    // naturalWidth is 0 under jsdom (never loads) → rescued to eager.
    expect(img.loading).toBe('eager');
  });

  it('leaves off-screen images deferred (no eager upgrade until they intersect)', () => {
    const img = document.createElement('img');
    img.setAttribute('loading', 'lazy');
    img.setAttribute('src', 'poster.jpg');
    document.body.appendChild(img);

    cleanup = installLazyImageRescue();
    triggerIntersection(img, false);
    // Not intersecting → left deferred, never upgraded to eager.
    expect(img.loading).not.toBe('eager');
  });

  it('observes lazy images added to the DOM later (async-rendered content)', async () => {
    cleanup = installLazyImageRescue();

    const img = document.createElement('img');
    img.setAttribute('loading', 'lazy');
    img.setAttribute('src', 'late.jpg');
    document.body.appendChild(img);

    // MutationObserver callbacks are microtask-scheduled.
    await Promise.resolve();
    await new Promise((r) => setTimeout(r, 0));
    expect(observed).toContain(img);
  });

  it('cleanup disconnects observers', () => {
    const img = document.createElement('img');
    img.setAttribute('loading', 'lazy');
    img.setAttribute('src', 'poster.jpg');
    document.body.appendChild(img);

    cleanup = installLazyImageRescue();
    expect(observed).toContain(img);
    cleanup();
    expect(observed).toHaveLength(0);
  });
});
