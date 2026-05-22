import React, { ReactNode, useEffect } from 'react';
import Navbar from './Navbar';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { motion, AnimatePresence } from 'framer-motion';
import { useLocation } from 'react-router-dom';
import { queryClient } from '../utils/queryClient';
import { useCustomConfig } from '../features/utils/hooks/useCustomConfig';
import { pageVariants } from './ui/animations';

const Footer: React.FC = () => (
  <footer className="py-8 text-center text-gray-500 text-xs">
    &copy; 2026 Animetix Team - World Class SPA
  </footer>
);

interface LayoutProps {
  children: ReactNode;
}

const LayoutContent: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { config } = useCustomConfig();
  const location = useLocation();

  useEffect(() => {
    if (config?.visual_theme) {
      const themes = ['theme-naruto', 'theme-manga-classic'];
      document.documentElement.classList.remove(...themes);
      if (config.visual_theme !== 'default') {
        document.documentElement.classList.add(`theme-${config.visual_theme}`);
      }
    }
  }, [config?.visual_theme]);

  return (
    <div className="min-h-screen flex flex-col transition-colors duration-500">
      <Navbar />
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
