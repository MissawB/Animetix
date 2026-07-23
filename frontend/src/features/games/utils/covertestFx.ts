export type FxKind =
  | 'invert'
  | 'grayscale'
  | 'hue'
  | 'sepia'
  | 'saturate'
  | 'contrast'
  | 'bright'
  | 'posterize';

export const FX_KINDS: FxKind[] = [
  'invert',
  'grayscale',
  'hue',
  'sepia',
  'saturate',
  'contrast',
  'bright',
  'posterize',
];

export type FxCombo = { kind: FxKind; seed: number }[];

// 2–4 distinct effects, each with its own random seed for intensity/direction.
export const pickFxCombo = (): FxCombo => {
  const shuffled = [...FX_KINDS].sort(() => Math.random() - 0.5);
  // Keep at most one of the two invert-based effects so they don't cancel out.
  const filtered: FxKind[] = [];
  let hasInvert = false;
  for (const k of shuffled) {
    const inverty = k === 'invert' || k === 'posterize';
    if (inverty && hasInvert) continue;
    if (inverty) hasInvert = true;
    filtered.push(k);
  }
  const count = 2 + Math.floor(Math.random() * 3); // 2..4
  return filtered.slice(0, count).map((kind) => ({ kind, seed: Math.random() }));
};

export const fxFragment = (kind: FxKind, L: number, seed: number): string => {
  switch (kind) {
    case 'invert':
      return `invert(${L.toFixed(2)})`;
    case 'grayscale':
      return `grayscale(${L.toFixed(2)})`;
    case 'hue':
      return `hue-rotate(${Math.round(L * (140 + seed * 220))}deg)`;
    case 'sepia':
      return `sepia(${L.toFixed(2)})`;
    case 'saturate':
      return `saturate(${(1 + L * (2.5 + seed * 4)).toFixed(2)})`;
    case 'contrast':
      return `contrast(${(1 + L * (0.7 + seed * 1.8)).toFixed(2)})`;
    // brightness: randomly darken or wash out depending on the seed.
    case 'bright':
      return `brightness(${(1 + L * (seed < 0.5 ? -(0.2 + seed * 0.7) : 0.35 + seed * 0.9)).toFixed(2)})`;
    // posterize-ish: harsh invert + heavy contrast for a solarised look.
    case 'posterize':
      return `invert(${(L * 0.9).toFixed(2)}) contrast(${(1 + L * 1.4).toFixed(2)})`;
    default:
      return '';
  }
};

export const fxFilter = (combo: FxCombo, level: number, blurPx: number): string => {
  const L = Math.max(0, Math.min(1, level)); // 1 = hardest, 0 = revealed
  const parts = combo.map(({ kind, seed }) => fxFragment(kind, L, seed)).filter(Boolean);
  parts.push(`blur(${blurPx}px)`);
  return parts.join(' ');
};
