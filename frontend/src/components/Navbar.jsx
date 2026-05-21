import React from 'react';
import { Link } from 'react-router-dom';
import { useUI } from '../context/UIContext';
import { Menu, Shield } from 'lucide-react';

const Navbar = () => {
  const { toggleSidebar } = useUI();
  
  return (
    <nav className="px-6 md:px-12 py-6 flex items-center justify-between sticky top-0 bg-white/80 dark:bg-navy-950/80 backdrop-blur-md z-50">
      <div className="flex items-center gap-6">
        <button className="bg-black text-white p-2 rounded-xl hover:scale-110 transition lg:hidden" onClick={toggleSidebar}>
          <Menu className="w-5 h-5" />
        </button>
        <Link to="/" className="flex items-center no-underline">
          <span className="font-black text-xl italic tracking-tighter">ANIMETIX</span>
        </Link>
        <Link to="/transparency/" className="hidden md:flex items-center gap-2 no-underline text-xs font-black italic text-gray-500 hover:text-yellow-600 transition-all ml-4">
          <Shield className="w-4 h-4" /> TRANSPARENCE
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;
