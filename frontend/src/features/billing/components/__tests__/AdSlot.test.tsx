import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { AdSlot } from '../AdSlot';
import { useAdPreferenceStore } from '../../../../store/adPreferenceStore';
import { logAdEvent } from '../../services/billingService';

vi.mock('../../services/billingService', () => ({ logAdEvent: vi.fn() }));

describe('AdSlot ad-preference gating', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAdPreferenceStore.setState({ adsEnabled: true });
  });

  it('when ads are enabled, renders content and logs an impression', () => {
    const { container } = render(<AdSlot label="Publicité" />);
    expect(container.firstChild).not.toBeNull();
    expect(logAdEvent).toHaveBeenCalledWith('impression', 'banner');
  });

  it('when ads are disabled, renders null and does NOT log an impression', () => {
    useAdPreferenceStore.setState({ adsEnabled: false });
    const { container } = render(<AdSlot label="Publicité" />);
    expect(container.firstChild).toBeNull();
    expect(logAdEvent).not.toHaveBeenCalled();
  });
});
