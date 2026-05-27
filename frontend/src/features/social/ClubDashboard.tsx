import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, Users, Settings, Bell, Info } from 'lucide-react';
import ClubChat from './components/ClubChat';

interface Member {
  id: string;
  username: string;
  avatar?: string;
  role: 'admin' | 'moderator' | 'member';
  status: 'online' | 'offline';
}

const ClubDashboard: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [clubName, setClubName] = useState('Loading...');
  const [members, setMembers] = useState<Member[]>([]);

  useEffect(() => {
    // Mock fetch
    setClubName('Shonen Jump Enthusiasts');
    setMembers([
      { id: '1', username: 'MissawB', role: 'admin', status: 'online' },
      { id: '2', username: 'Alice', role: 'moderator', status: 'online' },
      { id: '3', username: 'Bob', role: 'member', status: 'offline' },
      { id: '4', username: 'Charlie', role: 'member', status: 'online' },
    ]);
  }, [id]);

  return (
    <div className="h-[calc(100vh-80px)] bg-gray-50 dark:bg-navy-950 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 bg-white dark:bg-navy-900 border-b border-gray-100 dark:border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/clubs" className="p-2 hover:bg-gray-100 dark:hover:bg-navy-800 rounded-xl transition-colors">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-black italic tracking-tighter uppercase">{clubName}</h1>
            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest flex items-center gap-1.5">
              <Users className="w-3 h-3" /> {members.length} members
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-navy-800 rounded-xl transition-colors text-gray-500">
            <Bell className="w-5 h-5" />
          </button>
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-navy-800 rounded-xl transition-colors text-gray-500">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 p-4 lg:p-6 overflow-hidden">
          <ClubChat clubId={id || ''} clubName={clubName} />
        </div>

        {/* Sidebar - Members & Info */}
        <div className="hidden lg:flex w-80 flex-col border-l border-gray-100 dark:border-white/5 bg-white dark:bg-navy-900 overflow-hidden">
          <div className="p-6 space-y-8 overflow-y-auto">
            {/* Club Info */}
            <div className="space-y-3">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-gray-400 flex items-center gap-2">
                <Info className="w-3 h-3" /> About Club
              </h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                A community for fans of Weekly Shonen Jump to discuss ongoing series, news, and theories.
              </p>
            </div>

            {/* Member List */}
            <div className="space-y-4">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-gray-400 flex items-center gap-2">
                <Users className="w-3 h-3" /> Members — {members.filter(m => m.status === 'online').length} Online
              </h3>
              <div className="space-y-2">
                {members.map(member => (
                  <div key={member.id} className="flex items-center justify-between p-2 rounded-xl hover:bg-gray-50 dark:hover:bg-navy-800 transition-colors group">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                          {member.username[0]}
                        </div>
                        <div className={`absolute -bottom-1 -right-1 w-3 h-3 border-2 border-white dark:border-navy-900 rounded-full ${
                          member.status === 'online' ? 'bg-green-500' : 'bg-gray-400'
                        }`} />
                      </div>
                      <div>
                        <p className="text-sm font-bold">{member.username}</p>
                        <p className={`text-[9px] font-black uppercase tracking-widest ${
                          member.role === 'admin' ? 'text-red-500' : member.role === 'moderator' ? 'text-blue-500' : 'text-gray-400'
                        }`}>
                          {member.role}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClubDashboard;
