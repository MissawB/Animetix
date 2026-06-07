import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, Calendar, Clock, MapPin, Users, Send, CheckCircle } from 'lucide-react';
import { getClubEventDetails, getClubDetails, toggleEventParticipation, ClubEvent } from '../../api';
import { useToastStore } from '../../../store/toastStore';
import { Button } from '../../../components/ui/Button';
import { Card } from '../../../components/ui/Card';

const ClubEventPage: React.FC = () => {
  const { id, eventId } = useParams<{ id: string; eventId: string }>();
  const [event, setEvent] = useState<ClubEvent | null>(null);
  const [clubName, setClubName] = useState('Chargement...');
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const [isEventPast, setIsEventPast] = useState(false);
  const [isParticipating, setIsParticipating] = useState(false);
  const [participantsCount, setParticipantsCount] = useState(0);
  const [chatMessages, setChatMessages] = useState<{ sender: string; text: string; time: string }[]>([
    { sender: 'IA Guide', text: "Bienvenue dans l'événement ! N'hésitez pas à poser vos questions ici.", time: "Système" },
  ]);
  const [newMessage, setNewMessage] = useState('');

  const fetchEventData = async () => {
    if (!eventId || !id) return;
    try {
      const eventData = await getClubEventDetails(Number(eventId));
      setEvent(eventData);
      setIsParticipating(!!eventData.is_participant);
      setParticipantsCount(eventData.participants_count || 0);

      const clubData = await getClubDetails(Number(id));
      setClubName(clubData.name);
    } catch (err) {
      console.error("Erreur de récupération :", err);
      useToastStore.getState().addToast("Impossible de récupérer l'événement.", "error");
    }
  };

  useEffect(() => {
    fetchEventData();
  }, [id, eventId]);

  // Countdown timer logic
  useEffect(() => {
    if (!event) return;

    const timer = setInterval(() => {
      const difference = +new Date(event.event_date) - +new Date();
      if (difference <= 0) {
        setIsEventPast(true);
        clearInterval(timer);
      } else {
        setIsEventPast(false);
        setTimeLeft({
          days: Math.floor(difference / (1000 * 60 * 60 * 24)),
          hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
          minutes: Math.floor((difference / 1000 / 60) % 60),
          seconds: Math.floor((difference / 1000) % 60),
        });
      }
    }, 1000);

    return () => clearInterval(timer);
  }, [event]);

  const handleToggleParticipation = async () => {
    if (!eventId) return;
    try {
      const response = await toggleEventParticipation(Number(eventId));
      setIsParticipating(response.status === 'joined');
      setParticipantsCount(response.participants_count);
      useToastStore.getState().addToast(
        response.status === 'joined' ? "Votre inscription a été enregistrée !" : "Vous ne participez plus à cet événement.",
        response.status === 'joined' ? "success" : "info"
      );
    } catch (err: any) {
      useToastStore.getState().addToast(err.error || "Action impossible. Êtes-vous membre du club ?", "error");
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setChatMessages(prev => [
      ...prev,
      {
        sender: 'Moi',
        text: newMessage,
        time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      }
    ]);
    setNewMessage('');
  };

  if (!event) {
    return (
      <div className="p-20 text-center text-white font-black animate-pulse uppercase tracking-[0.3em] bg-navy-950 min-h-screen">
        Chargement des détails de l'événement...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-navy-950 text-surface-text py-12 px-6">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Back Link */}
        <Link 
          to={`/clubs/${id}/`} 
          className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-gray-500 hover:text-brand-primary no-underline transition-colors"
        >
          <ChevronLeft className="w-4 h-4" /> Retour au club : {clubName}
        </Link>

        {/* Hero Section */}
        <Card hasAura className="relative overflow-hidden p-8 md:p-12 bg-gradient-to-br from-white to-gray-50 dark:from-navy-900 dark:to-navy-950 border border-gray-100 dark:border-white/5 rounded-3xl flex flex-col md:flex-row gap-8 justify-between items-start md:items-center">
          <div className="space-y-6 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-primary/10 border border-brand-primary/20 text-brand-primary text-[10px] font-black uppercase tracking-widest">
              <Calendar className="w-3.5 h-3.5" /> Événement du Club
            </div>
            <h1 className="text-4xl md:text-5xl font-black italic tracking-tighter uppercase leading-none manga-font text-brand-accent">{event.title}</h1>
            <p className="text-sm text-gray-400 font-bold leading-relaxed">{event.description}</p>
            
            <div className="flex flex-wrap gap-4 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-brand-primary" />
                {new Date(event.event_date).toLocaleDateString('fr-FR', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </span>
              <span className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-brand-primary" /> Salon Vocal de l'App
              </span>
              <span className="flex items-center gap-1.5">
                <Users className="w-4 h-4 text-brand-primary" /> {participantsCount} inscrits
              </span>
            </div>
          </div>

          {/* Countdown / Status Box */}
          <div className="w-full md:w-80 bg-gray-100/50 dark:bg-navy-950/50 border border-gray-200 dark:border-white/5 rounded-2xl p-6 text-center space-y-4">
            {isEventPast ? (
              <div className="space-y-2">
                <span className="inline-flex items-center gap-1 text-[10px] bg-red-500/10 text-red-500 font-black tracking-widest uppercase px-3 py-1 rounded-full">
                  Terminé
                </span>
                <p className="text-sm font-bold text-gray-500">Cet événement est passé.</p>
              </div>
            ) : (
              <div className="space-y-4">
                <span className="inline-flex items-center gap-1 text-[10px] bg-green-500/10 text-green-500 font-black tracking-widest uppercase px-3 py-1 rounded-full">
                  À venir
                </span>
                
                {/* Timer Grid */}
                <div className="grid grid-cols-4 gap-2">
                  <div className="bg-white dark:bg-navy-900 rounded-xl p-2.5 border border-gray-200 dark:border-white/5">
                    <span className="block text-xl font-black text-brand-primary">{timeLeft.days}</span>
                    <span className="text-[8px] font-black uppercase text-gray-400">Jours</span>
                  </div>
                  <div className="bg-white dark:bg-navy-900 rounded-xl p-2.5 border border-gray-200 dark:border-white/5">
                    <span className="block text-xl font-black text-brand-primary">{timeLeft.hours}</span>
                    <span className="text-[8px] font-black uppercase text-gray-400">Heures</span>
                  </div>
                  <div className="bg-white dark:bg-navy-900 rounded-xl p-2.5 border border-gray-200 dark:border-white/5">
                    <span className="block text-xl font-black text-brand-primary">{timeLeft.minutes}</span>
                    <span className="text-[8px] font-black uppercase text-gray-400">Min</span>
                  </div>
                  <div className="bg-white dark:bg-navy-900 rounded-xl p-2.5 border border-gray-200 dark:border-white/5">
                    <span className="block text-xl font-black text-brand-primary">{timeLeft.seconds}</span>
                    <span className="text-[8px] font-black uppercase text-gray-400">Sec</span>
                  </div>
                </div>

                <Button 
                  onClick={handleToggleParticipation}
                  className={`w-full py-4 font-black uppercase tracking-widest rounded-xl transition-all border-none cursor-pointer flex items-center justify-center gap-2 ${
                    isParticipating 
                      ? 'bg-green-500 hover:bg-green-600 text-white shadow-lg' 
                      : 'bg-brand-primary hover:bg-brand-primary/95 text-white'
                  }`}
                >
                  {isParticipating ? (
                    <>
                      <CheckCircle className="w-4 h-4" /> Inscrit(e) !
                    </>
                  ) : (
                    "Rejoindre l'événement"
                  )}
                </Button>
              </div>
            )}
          </div>
        </Card>

        {/* Dual Panel - Info & Discussion */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Left / Center Column: Chat & Discussion */}
          <div className="md:col-span-2 space-y-6 flex flex-col h-[500px] bg-white dark:bg-navy-900 border border-gray-100 dark:border-white/5 rounded-3xl overflow-hidden p-6">
            <h3 className="text-sm font-black uppercase tracking-wider text-gray-400 flex items-center gap-2 pb-4 border-b border-gray-100 dark:border-white/5">
              Fil de discussion de l'événement
            </h3>
            
            {/* Messages */}
            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              {chatMessages.map((msg, i) => (
                <div 
                  key={i} 
                  className={`flex flex-col max-w-[80%] space-y-1 ${
                    msg.sender === 'Moi' ? 'ml-auto items-end' : 'mr-auto items-start'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-gray-500">{msg.sender}</span>
                    <span className="text-[9px] text-gray-400">{msg.time}</span>
                  </div>
                  <div className={`p-3.5 rounded-2xl text-xs font-bold ${
                    msg.sender === 'Moi' 
                      ? 'bg-brand-primary text-white rounded-tr-none' 
                      : 'bg-gray-100 dark:bg-navy-800 text-surface-text rounded-tl-none'
                  }`}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            {/* Input Form */}
            <form onSubmit={handleSendMessage} className="flex gap-2 pt-4 border-t border-gray-100 dark:border-white/5">
              <input
                type="text"
                placeholder="Posez vos questions ou discutez du concept..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                className="flex-1 bg-gray-50 dark:bg-navy-950 border border-gray-100 dark:border-white/5 p-4 rounded-xl text-xs font-bold focus:outline-none focus:border-brand-primary"
              />
              <button
                type="submit"
                className="p-4 bg-brand-primary hover:bg-brand-primary/95 text-white rounded-xl flex items-center justify-center transition-all border-none cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>

          {/* Right Column: Info & Status */}
          <div className="bg-white dark:bg-navy-900 border border-gray-100 dark:border-white/5 rounded-3xl p-6 space-y-6">
            <h3 className="text-sm font-black uppercase tracking-wider text-gray-400 flex items-center gap-2 pb-4 border-b border-gray-100 dark:border-white/5">
              Statistiques de l'IA
            </h3>
            
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 dark:bg-navy-800 rounded-2xl">
                <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-1">Impact prévu</p>
                <p className="text-lg font-black text-brand-primary">+250 XP</p>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-navy-800 rounded-2xl">
                <p className="text-[10px] font-black uppercase tracking-widest text-gray-400 mb-1">Vibe détectée</p>
                <p className="text-lg font-black text-purple-500">Social / Débat</p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default ClubEventPage;


