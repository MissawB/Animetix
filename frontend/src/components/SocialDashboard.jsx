import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, UserMinus, Heart } from 'lucide-react';

const SocialDashboard = () => {
  const [data, setData] = useState({ following: [], followers: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/v1/social/dashboard/')
      .then(res => res.json())
      .then(json => {
        setData(json);
        setLoading(false);
      })
      .catch(err => console.error("Error loading social dashboard:", err));
  }, []);

  const toggleFollow = async (userId) => {
    try {
      const response = await fetch(`/api/v1/social/${userId}/toggle_follow/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
      });
      if (response.ok) {
        window.location.reload(); 
      }
    } catch (err) {
      console.error("Error toggling follow:", err);
    }
  };

  if (loading) return <div>Chargement de l'espace communauté...</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
      {/* ABONNEMENTS */}
      <div className="bg-white dark:bg-navy-800 rounded-[2rem] p-8 shadow-xl border border-gray-100 dark:border-white/5">
        <h3 className="manga-font text-xl mb-6 flex items-center gap-3">
          <Users className="w-6 h-6 text-yellow-400" /> Mes Abonnements
        </h3>
        <div className="space-y-4">
          {data.following.map(f => (
            <div key={f.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl hover:scale-[1.02] transition-transform">
              <Link to={`/profile/${f.username}/`} className="flex items-center gap-4 no-underline text-current">
                <div className="w-12 h-12 bg-yellow-400 rounded-xl flex items-center justify-center font-black italic border-2 border-black">
                  {f.username[0].toUpperCase()}
                </div>
                <div>
                  <div className="font-bold">{f.username}</div>
                  <div className="text-[10px] uppercase font-black opacity-40">Niveau {f.level}</div>
                </div>
              </Link>
              <button onClick={() => toggleFollow(f.to_user)} className="btn btn-sm btn-outline-danger rounded-pill px-3">
                <UserMinus className="w-4 h-4" />
              </button>
            </div>
          ))}
          {data.following.length === 0 && <p className="text-center py-8 opacity-30 italic">Vous ne suivez personne pour le moment.</p>}
        </div>
      </div>

      {/* ABONNÉS */}
      <div className="bg-white dark:bg-navy-800 rounded-[2rem] p-8 shadow-xl border border-gray-100 dark:border-white/5">
        <h3 className="manga-font text-xl mb-6 flex items-center gap-3">
          <Heart className="w-6 h-6 text-red-500" /> Mes Abonnés
        </h3>
        <div className="space-y-4">
          {data.followers.map(f => (
            <div key={f.id} className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-navy-900 rounded-2xl">
              <div className="w-12 h-12 bg-navy-700 rounded-xl flex items-center justify-center font-black italic border-2 border-white/10">
                {f.username[0].toUpperCase()}
              </div>
              <div>
                <div className="font-bold">{f.username}</div>
                <div className="text-[10px] uppercase font-black opacity-40">Niveau {f.level}</div>
              </div>
            </div>
          ))}
          {data.followers.length === 0 && <p className="text-center py-8 opacity-30 italic">Aucun abonné pour le moment.</p>}
        </div>
      </div>
    </div>
  );
};

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

export default SocialDashboard;
