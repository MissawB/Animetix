import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import type { LabEntry } from '../labHubData';

/** Compact secondary-grid card shared by the Creative and Cognition sections;
 *  they differ only in the hover border accent (`hoverBorderClass`). */
export const LabHubCompactCard: React.FC<{ lab: LabEntry; hoverBorderClass: string }> = ({
  lab,
  hoverBorderClass,
}) => (
  <Link to={lab.url} className="no-underline group">
    <Card
      padding="none"
      className={`h-full bg-black/40 border-white/5 ${hoverBorderClass} transition-all duration-500 overflow-hidden relative group`}
    >
      <div
        className={`absolute inset-0 bg-gradient-to-br ${lab.bg} opacity-0 group-hover:opacity-100 transition-opacity duration-700`}
      />
      <div className="p-8 relative z-10">
        <div className="flex justify-between items-start mb-6">
          <div
            className={`p-3 rounded-xl bg-white/5 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500 ${lab.color}`}
          >
            <lab.icon className="w-6 h-6" />
          </div>
          <Badge
            variant="neutral"
            className="bg-white/5 border-none text-[7px] font-black italic uppercase tracking-widest"
          >
            {lab.badge}
          </Badge>
        </div>
        <h3 className="text-xl font-black italic manga-font uppercase mb-3 tracking-tighter group-hover:text-white transition-colors">
          {lab.title}
        </h3>
        <p className="text-[10px] font-bold opacity-30 uppercase leading-relaxed tracking-wider group-hover:opacity-60 transition-opacity">
          {lab.desc}
        </p>
      </div>
    </Card>
  </Link>
);
