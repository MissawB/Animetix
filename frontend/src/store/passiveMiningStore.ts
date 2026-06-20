import { create } from 'zustand';

interface PassiveMiningState {
  isEnabled: boolean;
  timeLeft: number; // in seconds
  totalMined: number;
  lastMinedAt: string | null;
  status: 'ONLINE' | 'COOLDOWN' | 'OFFLINE';
  setEnabled: (enabled: boolean) => void;
  setTimeLeft: (time: number) => void;
  setStatus: (status: 'ONLINE' | 'COOLDOWN' | 'OFFLINE') => void;
  incrementTotalMined: (amount: number) => void;
  setLastMinedAt: (date: string | null) => void;
}

export const usePassiveMiningStore = create<PassiveMiningState>((set) => ({
  isEnabled: localStorage.getItem('passive_mining_enabled') !== 'false',
  timeLeft: 180,
  totalMined: parseInt(localStorage.getItem('passive_mining_total') || '0', 10),
  lastMinedAt: localStorage.getItem('passive_mining_last_date'),
  status: 'OFFLINE',
  setEnabled: (enabled) => {
    localStorage.setItem('passive_mining_enabled', String(enabled));
    set({ isEnabled: enabled, status: enabled ? 'ONLINE' : 'OFFLINE' });
  },
  setTimeLeft: (time) => set({ timeLeft: time }),
  setStatus: (status) => set({ status }),
  incrementTotalMined: (amount) => set((state) => {
    const total = state.totalMined + amount;
    localStorage.setItem('passive_mining_total', String(total));
    return { totalMined: total };
  }),
  setLastMinedAt: (date) => {
    if (date) {
      localStorage.setItem('passive_mining_last_date', date);
    } else {
      localStorage.removeItem('passive_mining_last_date');
    }
    set({ lastMinedAt: date });
  }
}));
