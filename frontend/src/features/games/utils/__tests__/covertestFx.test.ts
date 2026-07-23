import { describe, it, expect } from 'vitest';
import { pickFxCombo, fxFragment, fxFilter } from '../covertestFx';

describe('covertestFx', () => {
  it('generates a combo of 2 to 4 effects', () => {
    const combo = pickFxCombo();
    expect(combo.length).toBeGreaterThanOrEqual(2);
    expect(combo.length).toBeLessThanOrEqual(4);
  });

  it('generates valid fxFragment filter strings', () => {
    expect(fxFragment('invert', 0.5, 0.2)).toBe('invert(0.50)');
    expect(fxFragment('grayscale', 1.0, 0.5)).toBe('grayscale(1.00)');
    expect(fxFragment('hue', 0.5, 0.5)).toContain('hue-rotate');
  });

  it('generates full css filter string including blur', () => {
    const combo = [{ kind: 'invert' as const, seed: 0.5 }];
    const filter = fxFilter(combo, 1, 10);
    expect(filter).toBe('invert(1.00) blur(10px)');
  });
});
