import React from 'react';

interface CyberSliderProps {
  min: number;
  max: number;
  value: number;
  onChange: (value: number) => void;
  color?: 'cyan' | 'magenta';
}

export const CyberSlider: React.FC<CyberSliderProps> = ({ min, max, value, onChange, color = 'cyan' }) => {
  const accentClass = color === 'cyan' ? 'accent-cyberpunk-neonCyan' : 'accent-cyberpunk-neonMagenta';
    return (
    <div className="w-full">
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label="Curseur de réglage"
        className={`w-full h-2 rounded-lg appearance-none cursor-pointer bg-cyberpunk-panelBorder ${accentClass}`}
      />
      <style>{`
        input[type=range]::-webkit-slider-thumb {
          -webkit-appearance: none;
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: #ffffff;
          box-shadow: 0 0 10px ${color === 'cyan' ? '#00F3FF' : '#FF00FF'};
        }
      `}</style>
    </div>
  );
};
