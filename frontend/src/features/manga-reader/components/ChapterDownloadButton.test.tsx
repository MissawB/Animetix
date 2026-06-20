import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ChapterDownloadButton } from './ChapterDownloadButton';
import * as hook from '../offline/useChapterDownload';

const CHAPTER = { id: 1, number: 1, title: 'Ch1', pages: [{ number: 0, image_url: 'u0' }] };

describe('ChapterDownloadButton', () => {
  beforeEach(() => vi.restoreAllMocks());

  it('shows a download action when idle and triggers download on click', async () => {
    const download = vi.fn();
    vi.spyOn(hook, 'useChapterDownload').mockReturnValue({
      status: 'idle', progress: 0, error: null, download, remove: vi.fn(),
    });
    render(<ChapterDownloadButton mediaId="m1" mediaTitle="T" chapter={CHAPTER} />);
    const btn = screen.getByRole('button', { name: /télécharger/i });
    await userEvent.click(btn);
    expect(download).toHaveBeenCalled();
  });

  it('shows progress percentage while downloading', () => {
    vi.spyOn(hook, 'useChapterDownload').mockReturnValue({
      status: 'downloading', progress: 0.42, error: null, download: vi.fn(), remove: vi.fn(),
    });
    render(<ChapterDownloadButton mediaId="m1" mediaTitle="T" chapter={CHAPTER} />);
    expect(screen.getByText('42%')).toBeInTheDocument();
  });

  it('shows a remove action when downloaded', async () => {
    const remove = vi.fn();
    vi.spyOn(hook, 'useChapterDownload').mockReturnValue({
      status: 'downloaded', progress: 1, error: null, download: vi.fn(), remove,
    });
    render(<ChapterDownloadButton mediaId="m1" mediaTitle="T" chapter={CHAPTER} />);
    const btn = screen.getByRole('button', { name: /supprimer/i });
    await userEvent.click(btn);
    expect(remove).toHaveBeenCalled();
  });
});
