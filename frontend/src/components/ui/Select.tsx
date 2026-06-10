import React from 'react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  ariaLabel?: string;
}

export const Select: React.FC<SelectProps> = ({ id, label, value, onChange, options, ariaLabel }) => {
  return (
    <div className="space-y-4">
      <label htmlFor={id} className="text-[10px] font-black opacity-30 uppercase tracking-[0.2em] px-2">{label}</label>
      <select
        id={id}
        aria-label={ariaLabel || label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-black border-2 border-white/5 rounded-2xl px-6 py-4 text-sm font-bold text-white outline-none focus:border-purple-500 transition-all"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>{option.label}</option>
        ))}
      </select>
    </div>
  );
};
