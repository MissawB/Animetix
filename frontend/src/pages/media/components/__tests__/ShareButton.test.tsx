import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { ShareButton } from '../ShareButton';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) =>
      typeof defaultValue === 'string' ? defaultValue : key,
  }),
}));

it('copies the current URL to the clipboard when navigator.share is unavailable', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.assign(navigator, { clipboard: { writeText } });
  render(<ShareButton title="Kimetsu no Yaiba" />);
  fireEvent.click(screen.getByRole('button', { name: /partager/i }));
  await waitFor(() => expect(writeText).toHaveBeenCalledWith(window.location.href));
  expect(screen.getByText(/lien copié/i)).toBeInTheDocument();
});
