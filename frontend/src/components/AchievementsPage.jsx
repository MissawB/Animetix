import React, { useState, useEffect } from 'react';
import { CheckCircle2, Trophy } from 'lucide-react';

const AchievementsPage = () => {
  const [achievements, setAchievements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/achievements/')
      .then(res => res.json())
      .then(json => {
        setAchievements(json);
        setLoading(false);
      })
      .catch(err => console.error("Error loading achievements:", err));
  }, []);

  if (loading) return <div className="text-center py-20">Chargement du grimoire...</div>;

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="text-center mb-12">
        <h1 className="manga-font text-5xl italic mb-2">📜 Grimoire des Hauts Faits</h1>
        <p className="text-gray-500">Votre légende s'écrit à chaque secret découvert.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {achievements.map((ach) => (
          <div key={ach.id} className={`p-6 rounded-[2rem] shadow-xl border border-gray-100 ${true ? 'bg-white' : 'bg-gray-50 opacity-70'}`}>
            <div className="flex items-center gap-4">
              <div className={`w-20 h-20 rounded-2xl flex items-center justify-center shadow-lg ${true ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
                {/* Fallback Trophy icon if dynamic icon is not found */}
                <Trophy className="w-8 h-8" />
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start mb-2">
                  <h5 className="manga-font text-sm uppercase">{ach.name}</h5>
                  <span className="text-xs px-2 py-1 rounded bg-gray-200">{ach.rarity}</span>
                </div>
                <p className="text-sm text-gray-600 mb-2">{ach.description}</p>
                <div className="text-green-600 font-bold text-xs flex items-center">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> {true ? "Débloqué" : `Verrouillé (+${ach.xp_reward} XP)`}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AchievementsPage;
