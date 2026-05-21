import React, { createContext, useContext, useState, useEffect } from 'react';
import soundManager from '../utils/SoundManager';

const UIContext = createContext();

export const UIProvider = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'auto');

  useEffect(() => {
    const html = document.documentElement;
    if (theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
  }, [theme]);

  const toggleSidebar = () => {
    soundManager.play('click');
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <UIContext.Provider value={{ isSidebarOpen, toggleSidebar, theme, setTheme, sounds: soundManager }}>
      {children}
    </UIContext.Provider>
  );
};

export const useUI = () => useContext(UIContext);
