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
