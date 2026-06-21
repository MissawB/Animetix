import { describe, it, expect, beforeEach } from 'vitest';
import { usePassiveMiningStore } from '../passiveMiningStore';

describe('usePassiveMiningStore', () => {
  beforeEach(() => {
    localStorage.clear();
    usePassiveMiningStore.setState({
      isEnabled: true,
      timeLeft: 180,
      totalMined: 0,
      lastMinedAt: null,
      status: 'OFFLINE',
    });
  });

  it('has sensible defaults', () => {
    const state = usePassiveMiningStore.getState();
    expect(state.timeLeft).toBe(180);
    expect(state.totalMined).toBe(0);
    expect(state.lastMinedAt).toBeNull();
    expect(state.status).toBe('OFFLINE');
  });

  it('setEnabled(true) sets status ONLINE and persists "true"', () => {
    usePassiveMiningStore.getState().setEnabled(true);
    const state = usePassiveMiningStore.getState();
    expect(state.isEnabled).toBe(true);
    expect(state.status).toBe('ONLINE');
    expect(localStorage.getItem('passive_mining_enabled')).toBe('true');
  });

  it('setEnabled(false) sets status OFFLINE and persists "false"', () => {
    usePassiveMiningStore.getState().setEnabled(false);
    const state = usePassiveMiningStore.getState();
    expect(state.isEnabled).toBe(false);
    expect(state.status).toBe('OFFLINE');
    expect(localStorage.getItem('passive_mining_enabled')).toBe('false');
  });

  it('setTimeLeft updates the countdown', () => {
    usePassiveMiningStore.getState().setTimeLeft(42);
    expect(usePassiveMiningStore.getState().timeLeft).toBe(42);
  });

  it('setStatus updates the status', () => {
    usePassiveMiningStore.getState().setStatus('COOLDOWN');
    expect(usePassiveMiningStore.getState().status).toBe('COOLDOWN');
  });

  it('incrementTotalMined accumulates and persists the running total', () => {
    usePassiveMiningStore.getState().incrementTotalMined(10);
    expect(usePassiveMiningStore.getState().totalMined).toBe(10);
    expect(localStorage.getItem('passive_mining_total')).toBe('10');

    usePassiveMiningStore.getState().incrementTotalMined(5);
    expect(usePassiveMiningStore.getState().totalMined).toBe(15);
    expect(localStorage.getItem('passive_mining_total')).toBe('15');
  });

  it('setLastMinedAt with a date persists it', () => {
    usePassiveMiningStore.getState().setLastMinedAt('2026-06-20');
    expect(usePassiveMiningStore.getState().lastMinedAt).toBe('2026-06-20');
    expect(localStorage.getItem('passive_mining_last_date')).toBe('2026-06-20');
  });

  it('setLastMinedAt(null) clears state and removes the persisted key', () => {
    localStorage.setItem('passive_mining_last_date', '2026-06-20');
    usePassiveMiningStore.setState({ lastMinedAt: '2026-06-20' });

    usePassiveMiningStore.getState().setLastMinedAt(null);
    expect(usePassiveMiningStore.getState().lastMinedAt).toBeNull();
    expect(localStorage.getItem('passive_mining_last_date')).toBeNull();
  });
});
