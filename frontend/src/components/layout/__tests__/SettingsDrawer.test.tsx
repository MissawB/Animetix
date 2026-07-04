import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SettingsDrawer from '../SettingsDrawer';
import { useAdPreferenceStore } from '../../../store/adPreferenceStore';

type Props = React.ComponentProps<typeof SettingsDrawer>;

const baseProps = (): Props => ({
  isSettingsOpen: true,
  theme: 'dark',
  currentLang: 'Français',
  toggleSettings: vi.fn(),
  setTheme: vi.fn(),
  setCurrentLang: vi.fn(),
});

describe('SettingsDrawer', () => {
  it('renders appearance and language sections', () => {
    render(<SettingsDrawer {...baseProps()} />);
    expect(screen.getByText('theme.light')).toBeInTheDocument();
    expect(screen.getByText('theme.dark')).toBeInTheDocument();
    expect(screen.getByText('theme.auto')).toBeInTheDocument();
    expect(screen.getByText('Français')).toBeInTheDocument();
    expect(screen.getByText('English')).toBeInTheDocument();
  });

  it('is translated to the open position when isSettingsOpen', () => {
    const { container } = render(<SettingsDrawer {...baseProps()} />);
    const aside = container.querySelector('#settings-drawer');
    expect(aside).toHaveClass('translate-x-0');
  });

  it('is translated off-screen when closed', () => {
    const { container } = render(
      <SettingsDrawer {...{ ...baseProps(), isSettingsOpen: false }} />,
    );
    const aside = container.querySelector('#settings-drawer');
    expect(aside).toHaveClass('translate-x-full');
  });

  it('calls toggleSettings(true) when the close button is clicked', () => {
    const props = baseProps();
    render(<SettingsDrawer {...props} />);
    fireEvent.click(screen.getByLabelText('Fermer les paramètres'));
    expect(props.toggleSettings).toHaveBeenCalledWith(true);
  });

  it('calls setTheme with the chosen theme', () => {
    const props = baseProps();
    render(<SettingsDrawer {...props} />);
    fireEvent.click(screen.getByText('theme.light'));
    expect(props.setTheme).toHaveBeenCalledWith('light');
  });

  it('calls setCurrentLang when a language is selected', () => {
    const props = baseProps();
    render(<SettingsDrawer {...props} />);
    fireEvent.click(screen.getByText('English'));
    expect(props.setCurrentLang).toHaveBeenCalledWith('English');
  });

  it('renders the ads section and reflects the store state', () => {
    useAdPreferenceStore.setState({ adsEnabled: true });
    render(<SettingsDrawer {...baseProps()} />);
    expect(screen.getByText('settings.ads')).toBeInTheDocument();
    expect(screen.getByLabelText('Basculer les publicités')).toBeInTheDocument();
  });

  it('toggling the ads switch flips the ad-preference store', () => {
    useAdPreferenceStore.setState({ adsEnabled: true });
    render(<SettingsDrawer {...baseProps()} />);
    fireEvent.click(screen.getByLabelText('Basculer les publicités'));
    expect(useAdPreferenceStore.getState().adsEnabled).toBe(false);
  });
});
