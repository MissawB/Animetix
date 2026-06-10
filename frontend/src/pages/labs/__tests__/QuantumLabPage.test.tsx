import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import QuantumLabPage from '../QuantumLabPage';
import React from 'react';

const mockMutate = vi.fn();

// Mock react-query
vi.mock('@tanstack/react-query', () => ({
  useMutation: vi.fn(() => ({
    mutate: mockMutate,
    isPending: false,
  })),
}));

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    h1: ({ children, ...props }: any) => <h1 {...props}>{children}</h1>,
    p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

describe('QuantumLabPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should have jitLevel and plasticity controls', () => {
    render(<QuantumLabPage />);
    expect(screen.getByLabelText(/JIT Level/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Plasticity/i)).toBeInTheDocument();
  });

  it('should call mutation with correct payload', () => {
    render(<QuantumLabPage />);
    fireEvent.click(screen.getByText(/EFFECTUER MESURE/i));
    
    expect(mockMutate).toHaveBeenCalledWith({
        action: 'quantum',
        theme: 'shonen',
        jitLevel: 'basic',
        plasticity: 'medium'
    });
  });
});
