import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import MultiverseLabPage from '../MultiverseLabPage';
import React from 'react';

const mockNavigate = vi.fn();

// Mock react-router-dom
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock react-query
vi.mock('@tanstack/react-query', () => ({
  useMutation: vi.fn(() => ({
    mutate: vi.fn(),
    isPending: false,
  })),
}));

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    h2: ({ children, ...props }: any) => <h2 {...props}>{children}</h2>,
    p: ({ children, ...props }: any) => <p {...props}>{children}</p>,
  },
  AnimatePresence: ({ children }: any) => <>{children}</>,
}));

// Mock personalization store
vi.mock('../../../store/personalizationStore', () => ({
  usePersonalizationStore: vi.fn((selector) => {
    const state = {
      config: { aura_type: 'none' },
      isPersonalizationEnabled: false,
    };
    return selector ? selector(state) : state;
  }),
}));

describe('MultiverseLabPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly and shows the gallery button', () => {
    render(
      <MemoryRouter>
        <MultiverseLabPage />
      </MemoryRouter>
    );
    
    // The i18n mock returns the translation key instead of the translated string
    expect(screen.getByText(/MULTIVERSE/i)).toBeInTheDocument();
    // Assuming 'labs.multiverse.gallery_btn' or similar is the key. Find by test id or index
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThanOrEqual(2);
  });

  it('navigates to gallery when the button is clicked', () => {
    render(
      <MemoryRouter>
        <MultiverseLabPage />
      </MemoryRouter>
    );
    
    const buttons = screen.getAllByRole('button');
    const galleryButton = buttons[1]; // The second button is the gallery button
    fireEvent.click(galleryButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/multiverse/gallery/');
  });
});
