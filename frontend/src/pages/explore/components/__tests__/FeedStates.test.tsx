import { render, screen, fireEvent } from '@testing-library/react';
import { FeedSkeleton, ErrorState, EmptyState } from '../FeedStates';

it('renders skeleton placeholders', () => {
  render(<FeedSkeleton />);
  expect(screen.getByTestId('feed-skeleton')).toBeInTheDocument();
});

it('calls onRetry when the retry button is clicked', () => {
  const onRetry = vi.fn();
  render(<ErrorState onRetry={onRetry} />);
  fireEvent.click(screen.getByRole('button', { name: /réessayer/i }));
  expect(onRetry).toHaveBeenCalledTimes(1);
});

it('shows a default empty message and a custom one', () => {
  const { rerender } = render(<EmptyState />);
  expect(screen.getByText(/aucune reco/i)).toBeInTheDocument();
  rerender(<EmptyState message="Rien ici" />);
  expect(screen.getByText('Rien ici')).toBeInTheDocument();
});
