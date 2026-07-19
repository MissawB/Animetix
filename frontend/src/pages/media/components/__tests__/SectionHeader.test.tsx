import { render, screen } from '@testing-library/react';
import { Tag } from 'lucide-react';
import { SectionHeader } from '../SectionHeader';

it('renders the title as a level-3 heading', () => {
  render(<SectionHeader title="Synopsis" icon={Tag} />);
  expect(screen.getByRole('heading', { level: 3, name: /synopsis/i })).toBeInTheDocument();
});

it('renders without an icon', () => {
  render(<SectionHeader title="Équipe" />);
  expect(screen.getByRole('heading', { level: 3, name: /équipe/i })).toBeInTheDocument();
});
