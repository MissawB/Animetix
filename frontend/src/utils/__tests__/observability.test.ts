import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as Sentry from '@sentry/react';
import posthog from 'posthog-js';
import { initObservability, trackEvent } from '../observability';

vi.mock('@sentry/react', () => ({
  init: vi.fn(),
  browserTracingIntegration: vi.fn(() => 'tracing'),
  replayIntegration: vi.fn(() => 'replay'),
}));

vi.mock('posthog-js', () => ({
  default: {
    init: vi.fn(),
    capture: vi.fn(),
  },
}));

describe('initObservability', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('does not init Sentry or PostHog when no env keys are set', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '');
    vi.stubEnv('VITE_POSTHOG_KEY', '');

    initObservability();

    expect(Sentry.init).not.toHaveBeenCalled();
    expect(posthog.init).not.toHaveBeenCalled();
  });

  it('initialises Sentry with the configured DSN when present', () => {
    vi.stubEnv('VITE_SENTRY_DSN', 'https://example@sentry.io/1');
    vi.stubEnv('VITE_POSTHOG_KEY', '');

    initObservability();

    expect(Sentry.init).toHaveBeenCalledTimes(1);
    expect(Sentry.init).toHaveBeenCalledWith(
      expect.objectContaining({
        dsn: 'https://example@sentry.io/1',
        tracesSampleRate: 1.0,
      }),
    );
    expect(posthog.init).not.toHaveBeenCalled();
  });

  it('initialises PostHog with the key and default host when present', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '');
    vi.stubEnv('VITE_POSTHOG_KEY', 'phc_test');
    vi.stubEnv('VITE_POSTHOG_HOST', '');

    initObservability();

    expect(posthog.init).toHaveBeenCalledWith(
      'phc_test',
      expect.objectContaining({
        api_host: 'https://eu.posthog.com',
        capture_pageview: true,
      }),
    );
  });

  it('uses a custom PostHog host when provided', () => {
    vi.stubEnv('VITE_POSTHOG_KEY', 'phc_test');
    vi.stubEnv('VITE_POSTHOG_HOST', 'https://us.posthog.com');

    initObservability();

    expect(posthog.init).toHaveBeenCalledWith(
      'phc_test',
      expect.objectContaining({ api_host: 'https://us.posthog.com' }),
    );
  });
});

describe('trackEvent', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('forwards the event name and properties to posthog.capture', () => {
    const props = { plan: 'pro', count: 3 };
    trackEvent('upgrade_clicked', props);
    expect(posthog.capture).toHaveBeenCalledWith('upgrade_clicked', props);
  });

  it('captures events with no properties', () => {
    trackEvent('page_view');
    expect(posthog.capture).toHaveBeenCalledWith('page_view', undefined);
  });
});
