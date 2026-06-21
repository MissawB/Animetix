import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { FeatureGate } from '../FeatureGate';
import { useFeatureFlag } from '../../../hooks/useFeatureFlag';

vi.mock('../../../hooks/useFeatureFlag', () => ({
  useFeatureFlag: vi.fn(),
}));

const useFeatureFlagMock = useFeatureFlag as ReturnType<typeof vi.fn>;

describe('FeatureGate', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders children when the flag is enabled', () => {
    useFeatureFlagMock.mockReturnValue(true);
    render(
      <FeatureGate flag="beta">
        <span>Beta content</span>
      </FeatureGate>,
    );
    expect(screen.getByText('Beta content')).toBeInTheDocument();
  });

  it('renders nothing (no children, no fallback) when the flag is disabled', () => {
    useFeatureFlagMock.mockReturnValue(false);
    render(
      <FeatureGate flag="beta">
        <span>Beta content</span>
      </FeatureGate>,
    );
    expect(screen.queryByText('Beta content')).not.toBeInTheDocument();
  });

  it('renders the fallback when the flag is disabled and a fallback is given', () => {
    useFeatureFlagMock.mockReturnValue(false);
    render(
      <FeatureGate flag="beta" fallback={<span>Fallback content</span>}>
        <span>Beta content</span>
      </FeatureGate>,
    );
    expect(screen.queryByText('Beta content')).not.toBeInTheDocument();
    expect(screen.getByText('Fallback content')).toBeInTheDocument();
  });

  it('renders nothing while the flag is loading (undefined)', () => {
    useFeatureFlagMock.mockReturnValue(undefined);
    render(
      <FeatureGate flag="beta" fallback={<span>Fallback content</span>}>
        <span>Beta content</span>
      </FeatureGate>,
    );
    // While loading, neither children nor fallback should render.
    expect(screen.queryByText('Beta content')).not.toBeInTheDocument();
    expect(screen.queryByText('Fallback content')).not.toBeInTheDocument();
  });

  it('passes the flag name through to useFeatureFlag', () => {
    useFeatureFlagMock.mockReturnValue(true);
    render(
      <FeatureGate flag="my-special-flag">
        <span>x</span>
      </FeatureGate>,
    );
    expect(useFeatureFlagMock).toHaveBeenCalledWith('my-special-flag');
  });
});
