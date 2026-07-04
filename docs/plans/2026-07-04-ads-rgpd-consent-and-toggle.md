# RGPD Ad Consent + Settings Ads Toggle — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add RGPD-compliant ad consent (Google Funding Choices + Consent Mode v2) and a client-side settings toggle that disables ads — which naturally pauses passive Bx mining.

**Architecture:** A new zustand+localStorage store (`adPreferenceStore`) holds `adsEnabled`. `AdSlot` reads it and renders `null` when disabled, so no ad mounts → `adSlotsVisible` stays 0 → `PassiveAdMiner` goes OFFLINE (no `/wallet/mine/` calls). A Consent Mode v2 default-denied snippet in `index.html` runs before AdSense loads; Google Funding Choices (enabled in the AdSense console) shows the EEA banner and updates consent. A new "Publicités" section in `SettingsDrawer` exposes the toggle + a "manage consent" link.

**Tech Stack:** React 19, Vite, TypeScript, zustand, vitest + @testing-library/react, Google AdSense (`adsbygoogle.js`) + Funding Choices.

Spec: `docs/specs/2026-07-04-ads-rgpd-consent-and-toggle-design.md`

## Global Constraints

- All work is in `frontend/`. No backend changes.
- Preference persistence is **client-side localStorage only** (key `ads_enabled`), mirroring `src/store/passiveMiningStore.ts`. Default = ads **enabled** (`true`).
- Stores are imported directly by components (like `AdSlot` imports `usePassiveMiningStore`) — do **not** thread new props through `Layout.tsx`/`SettingsDrawer` prop interface.
- Out of scope: new ad placements, backend/account sync, premium ad-free gating, fixing the pre-existing `/api/v1/billing/wallet/mine/` trust gap.
- Run tests with `npx vitest run <path>` from `frontend/`. i18n `t(key, fallback)` returns the **key** in tests (e.g. `screen.getByText('theme.light')`).
- Commit after each task.

---

### Task 1: Ad preference store

**Files:**
- Create: `frontend/src/store/adPreferenceStore.ts`
- Test: `frontend/src/store/__tests__/adPreferenceStore.test.ts`

**Interfaces:**
- Consumes: nothing.
- Produces: `useAdPreferenceStore` (zustand store) with state `{ adsEnabled: boolean; setAdsEnabled: (enabled: boolean) => void }`. localStorage key `ads_enabled` (`'true'`/`'false'`), default `true` when absent.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/store/__tests__/adPreferenceStore.test.ts`:

```ts
import { describe, it, expect, beforeEach } from 'vitest';
import { useAdPreferenceStore } from '../adPreferenceStore';

describe('useAdPreferenceStore', () => {
  beforeEach(() => {
    localStorage.clear();
    useAdPreferenceStore.setState({ adsEnabled: true });
  });

  it('defaults to ads enabled', () => {
    expect(useAdPreferenceStore.getState().adsEnabled).toBe(true);
  });

  it('setAdsEnabled(false) disables ads and persists "false"', () => {
    useAdPreferenceStore.getState().setAdsEnabled(false);
    expect(useAdPreferenceStore.getState().adsEnabled).toBe(false);
    expect(localStorage.getItem('ads_enabled')).toBe('false');
  });

  it('setAdsEnabled(true) re-enables ads and persists "true"', () => {
    useAdPreferenceStore.getState().setAdsEnabled(false);
    useAdPreferenceStore.getState().setAdsEnabled(true);
    expect(useAdPreferenceStore.getState().adsEnabled).toBe(true);
    expect(localStorage.getItem('ads_enabled')).toBe('true');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/store/__tests__/adPreferenceStore.test.ts`
Expected: FAIL — cannot resolve `../adPreferenceStore`.

- [ ] **Step 3: Write minimal implementation**

Create `frontend/src/store/adPreferenceStore.ts`:

```ts
import { create } from 'zustand';

interface AdPreferenceState {
  // Whether ads are shown. Disabling ads also pauses passive Bx mining, because
  // AdSlot renders nothing when this is false (no ad mounted -> adSlotsVisible 0).
  adsEnabled: boolean;
  setAdsEnabled: (enabled: boolean) => void;
}

export const useAdPreferenceStore = create<AdPreferenceState>((set) => ({
  adsEnabled: localStorage.getItem('ads_enabled') !== 'false',
  setAdsEnabled: (enabled) => {
    localStorage.setItem('ads_enabled', String(enabled));
    set({ adsEnabled: enabled });
  },
}));
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/store/__tests__/adPreferenceStore.test.ts`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/store/adPreferenceStore.ts frontend/src/store/__tests__/adPreferenceStore.test.ts
git commit -m "feat(ads): client ad-preference store (localStorage)"
```

---

### Task 2: AdSlot honours the ads-disabled preference

**Files:**
- Modify: `frontend/src/features/billing/components/AdSlot.tsx`
- Test: `frontend/src/features/billing/components/__tests__/AdSlot.test.tsx` (create)

**Interfaces:**
- Consumes: `useAdPreferenceStore` from `src/store/adPreferenceStore` (Task 1); `usePassiveMiningStore` and `logAdEvent` (existing).
- Produces: `AdSlot` renders `null` and performs no impression/mining side-effects when `adsEnabled === false`.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/features/billing/components/__tests__/AdSlot.test.tsx`:

```tsx
import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AdSlot } from '../AdSlot';
import { useAdPreferenceStore } from '../../../../store/adPreferenceStore';
import { usePassiveMiningStore } from '../../../../store/passiveMiningStore';
import { logAdEvent } from '../../services/billingService';

vi.mock('../../services/billingService', () => ({ logAdEvent: vi.fn() }));

describe('AdSlot ad-preference gating', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAdPreferenceStore.setState({ adsEnabled: true });
    usePassiveMiningStore.setState({ adSlotsVisible: 0 });
  });

  it('when ads are enabled, renders content and registers an impression + mining', () => {
    const { container } = render(<AdSlot label="Publicité" />);
    expect(container.firstChild).not.toBeNull();
    expect(logAdEvent).toHaveBeenCalledWith('impression', 'banner');
    expect(usePassiveMiningStore.getState().adSlotsVisible).toBe(1);
  });

  it('when ads are disabled, renders null and does NOT register impression or mining', () => {
    useAdPreferenceStore.setState({ adsEnabled: false });
    const { container } = render(<AdSlot label="Publicité" />);
    expect(container.firstChild).toBeNull();
    expect(logAdEvent).not.toHaveBeenCalled();
    expect(usePassiveMiningStore.getState().adSlotsVisible).toBe(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/features/billing/components/__tests__/AdSlot.test.tsx`
Expected: FAIL — the disabled case still renders the placeholder and calls `logAdEvent` (AdSlot does not yet read the preference).

- [ ] **Step 3: Write minimal implementation**

In `frontend/src/features/billing/components/AdSlot.tsx`:

Add the import after the existing store import (line 3):

```tsx
import { useAdPreferenceStore } from '../../../store/adPreferenceStore';
```

Inside the component, after the `unregisterAd` selector (current line 53), add:

```tsx
  const adsEnabled = useAdPreferenceStore((s) => s.adsEnabled);
```

Replace the impression/mining effect (current lines 57-63) with:

```tsx
  // Impression tracking + mining registration for the lifetime of the slot.
  // Skipped entirely when the user has disabled ads.
  useEffect(() => {
    if (!adsEnabled) return;
    logAdEvent('impression', 'banner');
    if (fundsMining) registerAd();
    return () => {
      if (fundsMining) unregisterAd();
    };
  }, [adsEnabled, fundsMining, registerAd, unregisterAd]);
```

Replace the AdSense fill effect (current lines 66-74) with:

```tsx
  // Ask AdSense to fill the unit once the script is in place.
  useEffect(() => {
    if (!adsEnabled || !hasRealAds) return;
    loadAdSenseScript(ADSENSE_CLIENT as string);
    try {
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    } catch (e) {
      console.error('AdSense push failed', e);
    }
  }, [adsEnabled, hasRealAds]);
```

Immediately before the `if (!hasRealAds) {` placeholder return (current line 76), add:

```tsx
  // User disabled ads in settings: render nothing (this also pauses mining,
  // since no slot is mounted -> adSlotsVisible stays 0).
  if (!adsEnabled) return null;
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/features/billing/components/__tests__/AdSlot.test.tsx`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/billing/components/AdSlot.tsx frontend/src/features/billing/components/__tests__/AdSlot.test.tsx
git commit -m "feat(ads): AdSlot renders nothing when ads disabled (pauses mining)"
```

---

### Task 3: Settings "Publicités" toggle + manage-consent link

**Files:**
- Modify: `frontend/src/components/layout/SettingsDrawer.tsx`
- Test: `frontend/src/components/layout/__tests__/SettingsDrawer.test.tsx` (extend)

**Interfaces:**
- Consumes: `useAdPreferenceStore` (Task 1); `window.googlefc?.showRevocationMessage?.()` (provided at runtime by Funding Choices — Task 4/ops).
- Produces: a "Publicités" section in the settings drawer with an on/off toggle bound to `adsEnabled` and a "Gérer mon consentement" button.

- [ ] **Step 1: Write the failing test**

Append these tests inside the existing `describe('SettingsDrawer', ...)` block in `frontend/src/components/layout/__tests__/SettingsDrawer.test.tsx` (add the two imports at the top of the file first):

```tsx
import { useAdPreferenceStore } from '../../../store/adPreferenceStore';
// (keep existing imports)

  it('renders the ads section and reflects the store state', () => {
    useAdPreferenceStore.setState({ adsEnabled: true });
    render(<SettingsDrawer {...baseProps()} />);
    expect(screen.getByText('settings.ads', { exact: false })).toBeInTheDocument();
    expect(screen.getByLabelText('Basculer les publicités')).toBeInTheDocument();
  });

  it('toggling the ads switch flips the ad-preference store', () => {
    useAdPreferenceStore.setState({ adsEnabled: true });
    render(<SettingsDrawer {...baseProps()} />);
    fireEvent.click(screen.getByLabelText('Basculer les publicités'));
    expect(useAdPreferenceStore.getState().adsEnabled).toBe(false);
  });
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/components/layout/__tests__/SettingsDrawer.test.tsx`
Expected: FAIL — no element with label `Basculer les publicités`.

- [ ] **Step 3: Write minimal implementation**

In `frontend/src/components/layout/SettingsDrawer.tsx`:

Extend the existing lucide import on line 3 (do **not** add a second `from 'lucide-react'` line — eslint `import/no-duplicates` would flag it):

```tsx
import { X, Sun, Moon, Monitor, CheckCircle2, Megaphone, ShieldCheck } from 'lucide-react';
```

Then, after the import block, add the store import + a `googlefc` window type:

```tsx
import { useAdPreferenceStore } from '../../store/adPreferenceStore';

declare global {
  interface Window {
    googlefc?: { showRevocationMessage?: () => void };
  }
}
```

Inside the component body, after `const { t } = useTranslation();` (current line 17), add:

```tsx
  const adsEnabled = useAdPreferenceStore((s) => s.adsEnabled);
  const setAdsEnabled = useAdPreferenceStore((s) => s.setAdsEnabled);
```

Inside the `<div className="space-y-10">` container, after the Langue block (i.e. before its closing `</div>` at current line 87), add this new section:

```tsx
        <div>
          <p className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-6">
            {t('settings.ads', 'Publicités')}
          </p>
          <button
            onClick={() => setAdsEnabled(!adsEnabled)}
            aria-label="Basculer les publicités"
            aria-pressed={adsEnabled}
            className="w-full flex items-center justify-between p-4 rounded-2xl text-black dark:text-white hover:bg-white/50 dark:hover:bg-black/20 transition-all text-left"
          >
            <span className="flex items-center gap-3">
              <Megaphone className="w-5 h-5 text-yellow-500" />
              <span className="manga-font text-xs">
                {t('settings.adsToggle', 'Afficher les publicités')}
              </span>
            </span>
            <span
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                adsEnabled ? 'bg-green-500' : 'bg-gray-400/40'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  adsEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </span>
          </button>
          <p className="mt-3 text-[10px] leading-relaxed text-gray-400 px-1">
            {t(
              'settings.adsHint',
              'Désactiver les pubs met aussi en pause le minage passif de Bx.',
            )}
          </p>
          <button
            onClick={() => window.googlefc?.showRevocationMessage?.()}
            className="mt-3 w-full flex items-center gap-2 p-3 rounded-2xl text-gray-500 dark:text-gray-400 hover:bg-white/50 dark:hover:bg-black/20 transition-all text-left"
          >
            <ShieldCheck className="w-4 h-4" />
            <span className="manga-font text-[11px]">
              {t('settings.manageConsent', 'Gérer mon consentement')}
            </span>
          </button>
        </div>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/components/layout/__tests__/SettingsDrawer.test.tsx`
Expected: PASS (existing tests + 2 new).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/layout/SettingsDrawer.tsx frontend/src/components/layout/__tests__/SettingsDrawer.test.tsx
git commit -m "feat(ads): Publicités toggle + manage-consent link in settings"
```

---

### Task 4: Consent Mode v2 bootstrap in index.html

**Files:**
- Modify: `frontend/index.html`
- Test: `frontend/src/__tests__/consentBootstrap.test.ts` (create)

**Interfaces:**
- Consumes: nothing.
- Produces: a `<script>` in `<head>` that sets Consent Mode v2 defaults to `denied` for EEA/GB before any app or AdSense script loads.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/__tests__/consentBootstrap.test.ts`:

```ts
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npx vitest run src/__tests__/consentBootstrap.test.ts`
Expected: FAIL — `index.html` has no consent snippet yet.

- [ ] **Step 3: Write minimal implementation**

In `frontend/index.html`, add this `<script>` inside `<head>`, immediately after the `<title>` line and before `</head>`:

```html
    <!-- RGPD Consent Mode v2: default DENIED for EEA/UK until the CMP
         (Google Funding Choices) collects consent. Must run before adsbygoogle.js. -->
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag() { dataLayer.push(arguments); }
      gtag('consent', 'default', {
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied',
        analytics_storage: 'denied',
        region: ['EEA', 'GB'],
        wait_for_update: 500,
      });
    </script>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npx vitest run src/__tests__/consentBootstrap.test.ts`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/index.html frontend/src/__tests__/consentBootstrap.test.ts
git commit -m "feat(ads): Consent Mode v2 default-denied bootstrap (EEA/GB)"
```

---

### Task 5: Final verification (lint + full frontend test run)

**Files:** none (verification only).

- [ ] **Step 1: Type-check + lint**

Run: `cd frontend && npx tsc --noEmit && npx eslint src/store/adPreferenceStore.ts src/features/billing/components/AdSlot.tsx src/components/layout/SettingsDrawer.tsx`
Expected: no errors.

- [ ] **Step 2: Run the full affected test suite**

Run: `cd frontend && npx vitest run src/store/__tests__/adPreferenceStore.test.ts src/features/billing/components/__tests__/AdSlot.test.tsx src/components/layout/__tests__/SettingsDrawer.test.tsx src/__tests__/consentBootstrap.test.ts`
Expected: all PASS.

- [ ] **Step 3: Commit (if any lint fixes were needed)**

```bash
git add -A frontend/
git commit -m "chore(ads): lint/type fixes for consent + ads toggle"
```

---

## Ops steps (manual, outside this plan — do in the Google/AdSense console)

These are **not** code tasks and cannot be automated here, but are required for the feature to be legally effective in production:

1. AdSense console → **Confidentialité et messages (Privacy & messaging)** → create a **GDPR** message (Funding Choices), target **EEA + United Kingdom**, and **publish** it. This IS the Google-certified CMP; once published, the `adsbygoogle.js` already loaded by `AdSlot` shows the consent banner to EEA/UK visitors and populates `window.googlefc`.
2. Confirm `VITE_ADSENSE_CLIENT` / `VITE_ADSENSE_SLOT_*` are set in prod (already present in `frontend/.env.production`).
