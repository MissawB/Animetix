import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { Modal } from '../../../components/ui/Modal';
import { Card } from '../../../components/ui/Card';

interface LabListOverlayProps {
  category: string | null;
  labs: { id: string; title: string; url: string; desc: string }[];
  onClose: () => void;
}

export const LabListOverlay: React.FC<LabListOverlayProps> = ({ category, labs, onClose }) => {
  return (
    <Modal
      isOpen={Boolean(category)}
      onClose={onClose}
      size="xl"
      title={
        <span className="text-3xl font-black italic manga-font uppercase tracking-tighter text-white">
          Laboratoires <span className="text-red-600">{category}</span>
        </span>
      }
      contentClassName="bg-black/90 backdrop-blur-xl border-white/10 rounded-3xl"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
        {labs.map((lab) => (
          <Link key={lab.id} to={lab.url} className="no-underline group">
            <Card
              padding="lg"
              className="bg-white/5 border-white/10 hover:border-red-600/50 transition-all"
            >
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-xl font-black italic uppercase manga-font mb-2 group-hover:text-red-500 transition-colors">
                    {lab.title}
                  </h3>
                  <p className="text-xs opacity-40 uppercase font-bold tracking-wider">
                    {lab.desc}
                  </p>
                </div>
                <ArrowRight className="w-6 h-6 opacity-0 group-hover:opacity-100 transform translate-x-[-10px] group-hover:translate-x-0 transition-all text-red-500" />
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </Modal>
  );
};
