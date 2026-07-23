import React from 'react';

interface CyberSliderProps {
  min: number;
  max: number;
  value: number;
  onChange: (value: number) => void;
  /** Encres de la forge : 'magenta' = fer chaud (vermillon), 'cyan' = braise
   *  (or). Noms historiques conservés pour ne pas toucher les appelants. */
  color?: 'cyan' | 'magenta';
}

export const CyberSlider: React.FC<CyberSliderProps> = ({
  min,
  max,
  value,
  onChange,
  color = 'cyan',
}) => {
  const ink = color === 'magenta' ? '#E8442B' : '#FDB913';
  return (
    <div className="w-full">
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label="Curseur de réglage"
        style={{ accentColor: ink }}
        className="h-2 w-full cursor-pointer appearance-none rounded-full bg-[#F4F1E8]/10"
      />
      <style>{`
        input[type=range]::-webkit-slider-thumb {
          -webkit-appearance: none;
          height: 16px;
          width: 16px;
          border-radius: 50%;
          background: #F4F1E8;
          box-shadow: 0 0 10px ${ink};
        }
      `}</style>
    </div>
  );
};
