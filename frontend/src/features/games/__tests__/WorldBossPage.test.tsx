import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import WorldBossPage from '../WorldBossPage';

describe('WorldBossPage', () => {
  it('renders the epic raid title', () => {
    render(
      <MemoryRouter>
        <WorldBossPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/WORLD BOSS/i)).toBeInTheDocument();
  });
});
