import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, Users, Settings, Bell, Info, Calendar, Plus, Clock, FileText } from 'lucide-react';
import ClubChat from './components/ClubChat';
import { getClubDetails, createClubEvent, getClubEvents, ClubEvent } from '../../api';
import { useToastStore } from '../../store/toastStore';

interface Member {
  id: string;
  username: string;
  avatar?: string;
  role: 'admin' | 'moderator' | 'member';
  status: 'online' | 'offline';
}

const ClubDashboard: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [clubName, setClubName] = useState('Chargement...');
  const [description, setDescription] = useState('');
  const [theme, setTheme] = useState('');
  const [members, setMembers] = useState<Member[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'events'>('chat');
  const [events, setEvents] = useState<ClubEvent[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventDescription, setNewEventDescription] = useState('');
  const [newEventDate, setNewEventDate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchClubData = async () => {
    if (!id) return;
    try {
      const club = await getClubDetails(Number(id));
      setClubName(club.name);
      setDescription(club.description);
      setTheme(club.theme || '');
      
      const eventList = await getClubEvents(Number(id));
      setEvents(eventList);
    } catch (err) {
      console.error("Erreur lors de la récupération du club :", err);
    }
  };

  useEffect(() => {
    fetchClubData();
    // Simulation des membres
    setMembers([
      { id: '1', username: 'MissawB', role: 'admin', status: 'online' },
      { id: '2', username: 'Alice', role: 'moderator', status: 'online' },
      { id: '3', username: 'Bob', role: 'member', status: 'offline' },
      { id: '4', username: 'Charlie', role: 'member', status: 'online' },
    ]);
  }, [id]);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEventTitle || !newEventDate || !newEventDescription) {
      useToastStore.getState().addToast("Veuillez remplir tous les champs.", "error");
      return;
    }
    
    setIsSubmitting(true);
    try {
      await createClubEvent({
        club: Number(id),
        title: newEventTitle,
        description: newEventDescription,
        event_date: newEventDate,
      });
      useToastStore.getState().addToast("Événement créé avec succès !", "success");
      setNewEventTitle('');
      setNewEventDescription('');
      setNewEventDate('');
      setShowCreateModal(false);
      fetchClubData(); // Rafraîchir la liste
    } catch (err: any) {
      console.error(err);
      useToastStore.getState().addToast(err?.error || err?.message || "Erreur lors de la création de l'événement.", "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="h-[calc(100vh-80px)] bg-gray-50 dark:bg-navy-950 flex flex-col overflow-hidden text-surface-text">
      {/* Header */}
      <div className="px-6 py-4 bg-white dark:bg-navy-900 border-b border-gray-100 dark:border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/clubs" className="p-2 hover:bg-gray-100 dark:hover:bg-navy-800 rounded-xl transition-colors">
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl font-black italic tracking-tighter uppercase">{clubName}</h1>
            <div className="flex items-center gap-3">
              <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest flex items-center gap-1.5">
                <Users className="w-3 h-3" /> {members.length} membres
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-gray-300 dark:bg-navy-700" />
              <span className="text-[10px] text-brand-primary font-black uppercase tracking-widest">
                Catégorie : {theme || 'Général'}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Tabs Selector */}
          <div className="flex bg-gray-100 dark:bg-navy-800 p-1 rounded-xl mr-4">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-2 text-xs font-black uppercase tracking-wider rounded-lg transition-all ${
                activeTab === 'chat'
                  ? 'bg-white dark:bg-navy-900 shadow-md text-brand-primary'
                  : 'text-gray-500 hover:text-gray-800 dark:hover:text-white'
              }`}
            >
              Discussion
            </button>
            <button
              onClick={() => setActiveTab('events')}
              className={`px-4 py-2 text-xs font-black uppercase tracking-wider rounded-lg transition-all ${
                activeTab === 'events'
                  ? 'bg-white dark:bg-navy-900 shadow-md text-brand-primary'
                  : 'text-gray-500 hover:text-gray-800 dark:hover:text-white'
              }`}
            >
              Événements ({events.length})
            </button>
          </div>

          <button className="p-2 hover:bg-gray-100 dark:hover:bg-navy-800 rounded-xl transition-colors text-gray-500">
            <Bell className="w-5 h-5" />
          </button>
          <button className="p-2 hover:bg-gray-100 dark:hover:bg-navy-800 rounded-xl transition-colors text-gray-500">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Active View: Chat */}
        {activeTab === 'chat' && (
          <div className="flex-1 p-4 lg:p-6 overflow-hidden">
            <ClubChat clubId={id || ''} clubName={clubName} />
          </div>
        )}

        {/* Active View: Events */}
        {activeTab === 'events' && (
          <div className="flex-1 p-6 overflow-y-auto space-y-6">
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-black italic tracking-tight uppercase">Événements programmés</h2>
                  <p className="text-xs text-gray-400 font-bold uppercase tracking-wider mt-1">Découvrez et rejoignez les activités organisées par le club.</p>
                </div>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="group relative bg-brand-primary text-white hover:scale-105 active:scale-95 px-5 py-3 rounded-xl font-black text-xs uppercase tracking-widest transition-all flex items-center gap-2 border-none cursor-pointer"
                >
                  <Plus className="w-4 h-4" /> Créer un événement
                </button>
              </div>

              {events.length === 0 ? (
                <div className="p-16 border-2 border-dashed border-gray-200 dark:border-white/5 rounded-3xl text-center space-y-4">
                  <Calendar className="w-12 h-12 text-gray-300 dark:text-navy-700 mx-auto" />
                  <p className="font-bold text-gray-500">Aucun événement n'est actuellement programmé pour ce club.</p>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="text-xs text-brand-primary font-black uppercase tracking-widest hover:underline border-none bg-transparent cursor-pointer"
                  >
                    Lancez le premier événement maintenant !
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {events.map((event) => (
                    <Link
                      key={event.id}
                      to={`/clubs/${id}/events/${event.id}`}
                      className="group bg-white dark:bg-navy-900 border border-gray-100 dark:border-white/5 hover:border-brand-primary/30 p-6 rounded-2xl shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all no-underline text-surface-text flex flex-col justify-between"
                    >
                      <div className="space-y-4">
                        <div className="flex items-start justify-between">
                          <span className="p-3 bg-brand-primary/10 rounded-xl text-brand-primary group-hover:scale-110 transition-transform">
                            <Calendar className="w-6 h-6" />
                          </span>
                          <span className="text-[10px] bg-gray-100 dark:bg-navy-800 text-gray-500 font-black tracking-widest uppercase px-3 py-1 rounded-full flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(event.event_date).toLocaleDateString('fr-FR', {
                              day: 'numeric',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </span>
                        </div>
                        <div className="space-y-2">
                          <h3 className="text-lg font-black uppercase tracking-tight group-hover:text-brand-primary transition-colors line-clamp-1">{event.title}</h3>
                          <p className="text-xs text-gray-400 leading-relaxed line-clamp-3">{event.description}</p>
                        </div>
                      </div>
                      <div className="pt-4 border-t border-gray-100 dark:border-white/5 flex items-center justify-between text-xs font-black uppercase tracking-widest text-brand-primary">
                        <span>Voir les détails</span>
                        <ChevronLeft className="w-4 h-4 rotate-180" />
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Sidebar - Members & Info */}
        <div className="hidden lg:flex w-80 flex-col border-l border-gray-100 dark:border-white/5 bg-white dark:bg-navy-900 overflow-hidden">
          <div className="p-6 space-y-8 overflow-y-auto">
            {/* Club Info */}
            <div className="space-y-3">
              <h3 className="text-xs font-black uppercase tracking-[0.2em] text-gray-400 flex items-center gap-2">
                <Info className="w-3 h-3" /> About Club
              </h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                {description || "Pas de description disponible pour ce club."}
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

      {/* Creation Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-navy-900 w-full max-w-lg rounded-3xl p-8 border border-gray-100 dark:border-white/5 space-y-6 shadow-2xl animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-gray-100 dark:border-white/5 pb-4">
              <h3 className="text-xl font-black italic uppercase tracking-tight">Planifier un événement</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-xs text-gray-400 font-bold hover:text-red-500 border-none bg-transparent cursor-pointer"
              >
                Fermer
              </button>
            </div>
            
            <form onSubmit={handleCreateEvent} className="space-y-6">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
                  <FileText className="w-3 h-3" /> Titre de l'événement
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ex : Soirée analyse Scan Shonen Jump 125"
                  value={newEventTitle}
                  onChange={(e) => setNewEventTitle(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-navy-950 border border-gray-100 dark:border-white/5 p-4 rounded-xl text-sm font-bold focus:outline-none focus:border-brand-primary"
                />
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
                  <Info className="w-3 h-3" /> Description de l'activité
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Expliquez le concept, le déroulement, ou les prérequis pour cet événement..."
                  value={newEventDescription}
                  onChange={(e) => setNewEventDescription(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-navy-950 border border-gray-100 dark:border-white/5 p-4 rounded-xl text-sm font-bold focus:outline-none focus:border-brand-primary resize-none"
                />
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
                  <Clock className="w-3 h-3" /> Date et Heure
                </label>
                <input
                  type="datetime-local"
                  required
                  value={newEventDate}
                  onChange={(e) => setNewEventDate(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-navy-950 border border-gray-100 dark:border-white/5 p-4 rounded-xl text-sm font-bold focus:outline-none focus:border-brand-primary"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-brand-primary text-white font-black py-4 rounded-xl text-xs uppercase tracking-widest hover:scale-[1.02] transition-transform flex items-center justify-center gap-2 border-none cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? "Création en cours..." : "Confirmer l'événement"}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClubDashboard;
