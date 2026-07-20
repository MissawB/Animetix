import { describe, it, expect } from 'vitest';
import { normalizeText } from '../normalizeText';

describe('normalizeText', () => {
  it('strips diacritics and lowercases', () => {
    expect(normalizeText('Sébastien')).toBe('sebastien');
    expect(normalizeText('ÉDWARD')).toBe('edward');
    expect(normalizeText('Jujutsu Kaïsen')).toBe('jujutsu kaisen');
  });

  it('leaves already-normalized text unchanged', () => {
    expect(normalizeText('naruto')).toBe('naruto');
  });

  it('does not trim surrounding whitespace (games compare raw tokens)', () => {
    expect(normalizeText('  Goku  ')).toBe('  goku  ');
  });

  it('handles the empty string', () => {
    expect(normalizeText('')).toBe('');
  });
});
