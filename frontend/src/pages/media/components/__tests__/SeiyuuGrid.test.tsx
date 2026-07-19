import { render, screen } from '@testing-library/react';
import { SeiyuuGrid } from '../SeiyuuGrid';

it('renders name, role and photo when image is present', () => {
  render(
    <SeiyuuGrid
      seiyuu={[{ id: 1, name: 'Natsuki Hanae', sample_url: '', image: 'x.jpg', role: 'Tanjiro' }]}
    />,
  );
  expect(screen.getByText('Natsuki Hanae')).toBeInTheDocument();
  expect(screen.getByText('Tanjiro')).toBeInTheDocument();
  expect(screen.getByAltText('Natsuki Hanae')).toHaveAttribute('src', 'x.jpg');
});

it('falls back to the initial letter when image is absent', () => {
  render(<SeiyuuGrid seiyuu={[{ id: 2, name: 'Akari Kito', sample_url: '' }]} />);
  expect(screen.getByText('Akari Kito')).toBeInTheDocument();
  expect(screen.queryByRole('img')).toBeNull();
  expect(screen.getByText('A')).toBeInTheDocument();
});
