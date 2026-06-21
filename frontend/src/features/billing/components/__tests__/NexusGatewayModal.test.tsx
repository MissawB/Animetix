import { render, screen, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { NexusGatewayModal } from '../NexusGatewayModal';

const tier = {
  id: 'pro',
  name: 'Nexus Pro',
  price: 29,
  features: ['Feature A', 'Feature B'],
};

describe('NexusGatewayModal', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
  });

  it('renders the idle confirmation state with tier details', () => {
    render(<NexusGatewayModal tier={tier} onClose={vi.fn()} onConfirm={vi.fn()} />);
    expect(screen.getByText('Confirmation Transaction')).toBeInTheDocument();
    expect(screen.getByText('Nexus Pro')).toBeInTheDocument();
    expect(screen.getByText('29€')).toBeInTheDocument();
    expect(screen.getByText('ACTIVER LE PROTOCOLE')).toBeInTheDocument();
  });

  it('calls onClose when the X button is clicked while idle', () => {
    const onClose = vi.fn();
    render(<NexusGatewayModal tier={tier} onClose={onClose} onConfirm={vi.fn()} />);
    const closeBtn = screen.getAllByRole('button').find((b) => b.textContent === '');
    fireEvent.click(closeBtn!);
    expect(onClose).toHaveBeenCalled();
  });

  it('transitions to processing then success on confirm', async () => {
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    render(<NexusGatewayModal tier={tier} onClose={vi.fn()} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByText('ACTIVER LE PROTOCOLE'));
    expect(screen.getByText('Initialisation...')).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500);
    });

    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(screen.getByText('Protocole Activé')).toBeInTheDocument();
  });

  it('returns to idle when onConfirm rejects', async () => {
    const onConfirm = vi.fn().mockRejectedValue(new Error('payment failed'));
    render(<NexusGatewayModal tier={tier} onClose={vi.fn()} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByText('ACTIVER LE PROTOCOLE'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500);
    });

    expect(screen.getByText('Confirmation Transaction')).toBeInTheDocument();
    expect(screen.queryByText('Protocole Activé')).not.toBeInTheDocument();
  });

  it('calls onClose from the success state CTA', async () => {
    const onClose = vi.fn();
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    render(<NexusGatewayModal tier={tier} onClose={onClose} onConfirm={onConfirm} />);

    fireEvent.click(screen.getByText('ACTIVER LE PROTOCOLE'));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500);
    });

    fireEvent.click(screen.getByText('ENTRER DANS LE NEXUS'));
    expect(onClose).toHaveBeenCalled();
  });
});
