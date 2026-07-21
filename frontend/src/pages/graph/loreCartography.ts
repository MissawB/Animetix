import React, { useState } from 'react';

// ── Domain ───────────────────────────────────────────────────────────────────

export interface LoreCommunity {
  id: string | number;
  name: string;
  summary: string;
  entities?: string[];
}

// The endpoint answers with EITHER the community list OR, while the map is being
// (re)built, a 202 `{status: "generating"}`. Both are 2xx, so apiClient hands them
// through as data — the page must discriminate. It used to assume an array and
// crashed the error boundary with "e?.map is not a function".
export type WorldMapResponse = LoreCommunity[] | { status?: string };

export const isGenerating = (data: WorldMapResponse | undefined): boolean =>
  !!data && !Array.isArray(data) && (data as { status?: string }).status === 'generating';

// ── Plate sizing ─────────────────────────────────────────────────────────────

/** The plate is landscape on a desktop and portrait on a phone: the SVG scales to
 *  the container width, so a landscape plate on a 390px screen would shrink every
 *  coast — and every label — to an unreadable sliver. */
export const LANDSCAPE = { w: 1000, h: 620 };
export const PORTRAIT = { w: 520, h: 660 };

const NARROW_QUERY = '(max-width: 1023px)';

// matchMedia is absent under jsdom and during SSR — fall back to the desktop plate
// rather than throwing.
const mediaQuery = () =>
  typeof window !== 'undefined' && typeof window.matchMedia === 'function'
    ? window.matchMedia(NARROW_QUERY)
    : null;

export const useNarrow = () => {
  const [narrow, setNarrow] = useState(() => mediaQuery()?.matches ?? false);
  React.useEffect(() => {
    const mq = mediaQuery();
    if (!mq) return undefined;
    const onChange = (e: MediaQueryListEvent) => setNarrow(e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);
  return narrow;
};

// ── Cartography ──────────────────────────────────────────────────────────────
// The map is drawn from the data alone: no coordinates are stored, so every shape
// is derived deterministically from the community's id (same data -> same map,
// every render). Only two things are encoded, and both are true: AREA = number of
// entities, CONTAINMENT = membership. Nothing is drawn between entities — we do
// not have those edges, and a map must not invent terrain.

export interface PlateSize {
  w: number;
  h: number;
}

export interface Territory {
  community: LoreCommunity;
  cx: number;
  cy: number;
  r: number;
  path: string;
  landmarks: { x: number; y: number; label: string }[];
}

/** Deterministic PRNG (mulberry32) seeded from a string. */
const seededRandom = (seed: string) => {
  let h = 1779033703 ^ seed.length;
  for (let i = 0; i < seed.length; i += 1) {
    h = Math.imul(h ^ seed.charCodeAt(i), 3432918353);
    h = (h << 13) | (h >>> 19);
  }
  let a = h >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

/** Organic coastline: jittered radial points closed into a smooth cubic path. */
const coastline = (cx: number, cy: number, r: number, rand: () => number) => {
  const points = 11;
  const pts = Array.from({ length: points }, (_, i) => {
    const angle = (i / points) * Math.PI * 2;
    const radius = r * (0.78 + rand() * 0.42);
    return [cx + Math.cos(angle) * radius, cy + Math.sin(angle) * radius * 0.82];
  });

  // Catmull-Rom -> bezier, wrapped, so the coast closes without a seam.
  const at = (i: number) => pts[(i + pts.length) % pts.length];
  let d = `M ${at(0)[0].toFixed(1)} ${at(0)[1].toFixed(1)}`;
  for (let i = 0; i < pts.length; i += 1) {
    const [x0, y0] = at(i - 1);
    const [x1, y1] = at(i);
    const [x2, y2] = at(i + 1);
    const [x3, y3] = at(i + 2);
    const c1 = [x1 + (x2 - x0) / 6, y1 + (y2 - y0) / 6];
    const c2 = [x2 - (x3 - x1) / 6, y2 - (y3 - y1) / 6];
    d += ` C ${c1[0].toFixed(1)} ${c1[1].toFixed(1)}, ${c2[0].toFixed(1)} ${c2[1].toFixed(1)}, ${x2.toFixed(1)} ${y2.toFixed(1)}`;
  }
  return `${d} Z`;
};

/** Lays the territories out: a golden-angle spiral seeds the composition, then a
 *  deterministic relaxation pushes overlapping landmasses apart. Territories must
 *  never touch — on a map, a shared coastline reads as a shared border, and the
 *  data says nothing about relations BETWEEN communities. */
export const surveyMap = (communities: LoreCommunity[], VIEW: PlateSize): Territory[] => {
  const GOLDEN = Math.PI * (3 - Math.sqrt(5));
  const count = communities.length;
  const spread = Math.min(VIEW.w, VIEW.h) * 0.34;
  const MARGIN = 26; // clear water + room for the label under each coast

  const nodes = communities.map((community, i) => {
    const entities = community.entities ?? [];
    // Area encodes the entity count -> the radius scales with its square root.
    const r = 40 + Math.sqrt(entities.length) * 20;
    const step = count === 1 ? 0 : Math.sqrt(i / Math.max(count - 1, 1));
    const angle = i * GOLDEN;
    return {
      community,
      r,
      x: VIEW.w / 2 + Math.cos(angle) * spread * step * 1.5,
      y: VIEW.h / 2 + Math.sin(angle) * spread * step,
    };
  });

  // The title cartouche is printed on the plate: treat it as an immovable island
  // so no coastline is ever drawn under the title.
  const cartouche = { x: VIEW.w * 0.13, y: VIEW.h * 0.1, r: VIEW.w < 700 ? 145 : 165 };

  for (let pass = 0; pass < 220; pass += 1) {
    for (let i = 0; i < nodes.length; i += 1) {
      for (let j = i + 1; j < nodes.length; j += 1) {
        const a = nodes[i];
        const b = nodes[j];
        const dx = b.x - a.x;
        const dy = b.y - a.y;
        const dist = Math.hypot(dx, dy) || 0.01;
        const min = a.r + b.r + MARGIN;
        if (dist < min) {
          const push = (min - dist) / 2;
          const ux = dx / dist;
          const uy = dy / dist;
          a.x -= ux * push;
          a.y -= uy * push;
          b.x += ux * push;
          b.y += uy * push;
        }
      }
    }

    nodes.forEach((n) => {
      // Push out of the cartouche (it never moves).
      const dx = n.x - cartouche.x;
      const dy = n.y - cartouche.y;
      const dist = Math.hypot(dx, dy) || 0.01;
      const min = n.r + cartouche.r;
      if (dist < min) {
        n.x += (dx / dist) * (min - dist);
        n.y += (dy / dist) * (min - dist);
      }
      // Keep every coast (and its label) inside the plate.
      n.x = Math.min(VIEW.w - n.r - 24, Math.max(n.r + 24, n.x));
      n.y = Math.min(VIEW.h - n.r - 44, Math.max(n.r + 30, n.y));
    });
  }

  return nodes.map(({ community, r, x: cx, y: cy }) => {
    const rand = seededRandom(String(community.id) + community.name);
    const entities = community.entities ?? [];

    const landmarks = entities.slice(0, 7).map((label) => {
      const a = rand() * Math.PI * 2;
      const d = Math.sqrt(rand()) * r * 0.5;
      return { x: cx + Math.cos(a) * d, y: cy + Math.sin(a) * d * 0.8, label };
    });

    return { community, cx, cy, r, path: coastline(cx, cy, r, rand), landmarks };
  });
};
