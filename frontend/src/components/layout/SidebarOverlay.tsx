import React from 'react';
import { useTranslation } from 'react-i18next';

interface SidebarOverlayProps {
  onClose: () => void;
}

const SidebarOverlay: React.FC<SidebarOverlayProps> = ({ onClose }) => {
  const { t } = useTranslation();
  return (
    <div
      id="sidebar-overlay"
      className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[1500]"
      onClick={onClose}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onClose();
        }
      }}
      role="button"
      tabIndex={0}
      aria-label={t('nav.close_overlays', 'Fermer les menus')}
    />
  );
};

export default React.memo(SidebarOverlay);
