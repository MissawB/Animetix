import React from 'react';
import Navbar from './Navbar';
import { UIProvider } from '../context/UIContext';

const Footer = () => (
  <footer className="py-8 text-center text-gray-500 text-xs">
    &copy; 2026 Animetix Team - Modernized SPA
  </footer>
);

const Layout = ({ children }) => {
  return (
    <UIProvider>
      <div className="min-h-screen bg-white dark:bg-navy-950 text-black dark:text-white flex flex-col">
        <Navbar />
        <main className="flex-grow">{children}</main>
        <Footer />
      </div>
    </UIProvider>
  );
};

export default Layout;
