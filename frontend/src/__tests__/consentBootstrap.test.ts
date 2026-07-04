import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// vitest runs with cwd = frontend/ (package root)
const html = readFileSync(resolve(process.cwd(), 'index.html'), 'utf-8');

describe('index.html Consent Mode v2 bootstrap', () => {
  it('declares default consent as denied before app load', () => {
    expect(html).toContain("gtag('consent', 'default'");
    expect(html).toContain("ad_storage: 'denied'");
    expect(html).toContain("ad_user_data: 'denied'");
    expect(html).toContain("ad_personalization: 'denied'");
  });

  it('scopes the denied default to the EEA / GB region', () => {
    expect(html).toContain("region: ['EEA', 'GB']");
  });
});
