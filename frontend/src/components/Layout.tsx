import React, { ReactNode, useCallback } from 'react';
import Navbar from './Navbar';
import AdminNavbar from './admin/AdminNavbar';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { queryClient } from '../utils/queryClient';
import { useCustomConfig } from '../features/utils/hooks/useCustomConfig';
import { pageVariants } from './ui/animations';
import CompanionOverlay from '../features/companion/CompanionOverlay';
import { useUIStore } from '../store/uiStore';
import { useAuthStore } from '../store/authStore';
import { Settings } from 'lucide-react';
import SidebarOverlay from './layout/SidebarOverlay';
import SidebarDrawer from './layout/SidebarDrawer';
import SettingsDrawer from './layout/SettingsDrawer';
import Footer from './layout/Footer';
import { useThemeSync } from './layout/useThemeSync';

interface LayoutProps {
  children: ReactNode;
}

const LayoutContent: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { config } = useCustomConfig();
  const location = useLocation();

  const {
    isSidebarOpen, isSettingsOpen, theme, currentLang,
    toggleSidebar, toggleSettings, setTheme, setCurrentLang
  } = useUIStore();

  const { user, isAuthenticated } = useAuthStore();

  useThemeSync(theme, config?.visual_theme);

  const handleOverlayClose = useCallback(() => {
    toggleSidebar(true);
    toggleSettings(true);
  }, [toggleSidebar, toggleSettings]);

  return (
    <div className="min-h-screen flex flex-col transition-colors duration-500">

      {/* OVERLAY (Visible when sidebar or settings drawer is open) */}
      {(isSidebarOpen || isSettingsOpen) && (
        <SidebarOverlay onClose={handleOverlayClose} />
      )}

      {/* SIDEBAR (DRAWER - LEFT) */}
      <SidebarDrawer
        isSidebarOpen={isSidebarOpen}
        isAuthenticated={isAuthenticated}
        user={user}
        pathname={location.pathname}
        toggleSidebar={toggleSidebar}
      />

      {/* SETTINGS DRAWER (RIGHT) */}
      <SettingsDrawer
        isSettingsOpen={isSettingsOpen}
        theme={theme}
        currentLang={currentLang}
        toggleSettings={toggleSettings}
        setTheme={setTheme}
        setCurrentLang={setCurrentLang}
      />

      {/* SETTINGS FLOATING BUTTON */}
      <button
        className="fixed bottom-6 left-6 w-14 h-14 bg-black text-yellow-400 dark:bg-[#0f0f1a] dark:text-white rounded-2xl shadow-2xl flex items-center justify-center text-3xl rotate-45 hover:rotate-0 transition-all duration-500 z-[800] group border border-black/10 dark:border-white/10"
        onClick={() => toggleSettings()}
        aria-label="Ouvrir les paramètres"
      >
        <Settings className="w-6 h-6 -rotate-45 group-hover:rotate-90 transition-transform duration-700" />
      </button>

      {/* NAVBAR */}
      <Navbar />

      {location.pathname.startsWith('/admin/') && <AdminNavbar />}

      {/* CONTENT WRAPPER */}
      <main className="flex-grow">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            variants={pageVariants}
            initial="initial"
            animate="animate"
            exit="exit"
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </main>

      <Footer />
      <CompanionOverlay />
    </div>
  );
};

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <QueryClientProvider client={queryClient}>
      <LayoutContent>{children}</LayoutContent>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
};

export default Layout;
