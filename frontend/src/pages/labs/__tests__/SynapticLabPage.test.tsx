// @vitest-environment jsdom

import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import SynapticLabPage from '../SynapticLabPage';
import React from 'react';

vi.stubGlobal('localStorage', {
  getItem: vi.fn(() => null),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
});

vi.mock('../../../store/personalizationStore', () => ({
  usePersonalizationStore: vi.fn((selector) => {
    const state = {
      config: { aura_type: 'none' },
      isPersonalizationEnabled: false,
    };
    return selector ? selector(state) : state;
  }),
}));

vi.mock('../../../utils/apiClient', () => ({
  apiClient: vi.fn(),
}));

vi.mock('../../../utils/firebase', () => ({
  auth: {
    currentUser: null,
  },
  app: {},
}));

const mockMutate = vi.fn();
const mockRefetch = vi.fn();

// Mock react-query
vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(() => ({
    data: {
      status: 'success',
      weights: Array(10).fill(0).map(() => Array(10).fill(0.1)),
      concepts: [
        'Shonen', 'Seinen', 'Cyberpunk', 'Mecha', 'Fantasy',
        'Magic', 'Ghibli', 'Romance', 'Comedy', 'Drama'
      ],
      plasticity_config: {
        tau_plus: 20.0,
        tau_minus: 20.0,
        num_concepts: 10
      },
      personalization_settings: {
        mode: 'auto',
        intensity_multiplier: 1.0,
        manual_archetype: 'shonen_hero',
        features: {
          aura: true,
          font: true,
          accent: true
        }
      },
      current_archetype: {
        id: 'shonen_hero',
        accent: '#FD7706',
        aura_type: 'fire',
        intensity: 0.8,
        font_vibe: 'brush'
      }
    },
    isLoading: false,
    isError: false,
    refetch: mockRefetch,
  })),
  useMutation: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
  })),
}));

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<React.HTMLAttributes<HTMLDivElement>>) => <div {...props}>{children}</div>,
  },
  AnimatePresence: ({ children }: React.PropsWithChildren<unknown>) => <>{children}</>,
}));

describe('SynapticLabPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders control elements and sliders correctly', () => {
    render(<SynapticLabPage />);
    expect(screen.getByLabelText(/LTP Time Constant/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/LTD Time Constant/i)).toBeInTheDocument();
  });

  it('triggers configuration updates when Apply is clicked', () => {
    render(<SynapticLabPage />);
    fireEvent.click(screen.getByText(/Apply Parameters/i));
    
    expect(mockMutate).toHaveBeenCalledWith({
      action: 'update_config',
      tau_plus: 20.0,
      tau_minus: 20.0,
      mode: 'auto',
      manual_archetype: 'shonen_hero',
      intensity_multiplier: 1.0,
      features: {
        aura: true,
        font: true,
        accent: true
      }
    });
  });
});
