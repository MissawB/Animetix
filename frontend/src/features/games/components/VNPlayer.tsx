import React, { useState, useEffect, useRef } from 'react';
import { ChevronRight, ChevronLeft } from 'lucide-react';
import { VNScene } from '../../../types';

interface VNPlayerProps {
  scenes: VNScene[];
}

export const VNPlayer: React.FC<VNPlayerProps> = ({ scenes }) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const currentScene = scenes[currentIndex];
  const dialogueRef = useRef(currentScene?.dialogue || '');

  useEffect(() => {
    if (!currentScene) return;
    
    // Check if dialogue has actually changed to avoid restart on same content
    if (dialogueRef.current === currentScene.dialogue && displayedText !== '') {
      return;
    }
    dialogueRef.current = currentScene.dialogue;

    setIsTyping(true);
    setDisplayedText('');
    let i = 0;
    const text = currentScene.dialogue;
    
    const interval = setInterval(() => {
      setDisplayedText((prev) => prev + text.charAt(i));
      i++;
      if (i >= text.length) {
        clearInterval(interval);
        setIsTyping(false);
      }
    }, 30);

    return () => clearInterval(interval);
  }, [currentIndex, currentScene, displayedText]);

  const nextScene = () => {
    if (isTyping) {
      setDisplayedText(currentScene.dialogue);
      setIsTyping(false);
    } else if (currentIndex < scenes.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const prevScene = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  if (!currentScene) return null;

  return (
    <div className="relative w-full aspect-video bg-black rounded-3xl overflow-hidden shadow-2xl border-4 border-white/10">
      {/* Background */}
      <img 
        src={currentScene.background_url} 
        className="absolute inset-0 w-full h-full object-cover transition-opacity duration-1000"
        alt="Background"
        loading="lazy"
        decoding="async"
      />
      
      {/* Character Sprite */}
      {currentScene.character_sprite_url && (
        <img 
          src={currentScene.character_sprite_url} 
          className="absolute bottom-0 left-1/2 -translate-x-1/2 h-4/5 object-contain transition-all duration-500 animate-in slide-in-from-bottom-10"
          alt={currentScene.character_name}
          loading="lazy"
          decoding="async"
        />
      )}

      {/* UI Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent pointer-events-none" />

      {/* Dialogue Box */}
      <div 
        className="absolute bottom-6 left-6 right-6 bg-black/60 backdrop-blur-md border border-white/20 p-8 rounded-3xl cursor-pointer pointer-events-auto"
        onClick={nextScene}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            nextScene();
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Passer à la scène suivante"
      >
        <div className="flex justify-between items-center mb-2">
          <span className="bg-anime-accent text-black px-4 py-1 rounded-full text-xs font-black uppercase tracking-widest">
            {currentScene.character_name}
          </span>
          <div className="flex gap-2">
            <button onClick={(e) => { e.stopPropagation(); prevScene(); }} className="p-1 hover:text-anime-accent"><ChevronLeft className="w-4 h-4" /></button>
            <button onClick={(e) => { e.stopPropagation(); nextScene(); }} className="p-1 hover:text-anime-accent"><ChevronRight className="w-4 h-4" /></button>
          </div>
        </div>
        <p className="text-xl font-medium text-white leading-relaxed min-h-[3rem]">
          {displayedText}
          {isTyping && <span className="inline-block w-2 h-5 bg-anime-accent ml-1 animate-pulse" />}
        </p>
      </div>

      {/* Progress Bar */}
      <div className="absolute top-0 left-0 w-full h-1 bg-white/10">
        <div 
          className="h-full bg-anime-accent transition-all duration-300"
          style={{ width: `${((currentIndex + 1) / scenes.length) * 100}%` }}
        />
      </div>
    </div>
  );
};
