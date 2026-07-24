import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronLeft, Calendar, Clock, MapPin, Users, Send, CheckCircle } from 'lucide-react';
import { socialService } from '../../features/social/services/socialService';
import { ClubEvent } from '../../types';
import { useToastStore } from '../../store/toastStore';
import { Button } from '../../components/ui/Button';
import { useTranslation } from 'react-i18next';

const ClubEventPage: React.FC = () => {
  const { t } = useTranslation();
  const { id, eventId } = useParams<{ id: string; eventId: string }>();
  const [event, setEvent] = useState<ClubEvent | null>(null);
  const [clubName, setClubName] = useState(t('social.club_event.loading', 'Chargement...'));
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const [isEventPast, setIsEventPast] = useState(false);
  const [isParticipating, setIsParticipating] = useState(false);
  const [participantsCount, setParticipantsCount] = useState(0);
  const [chatMessages, setChatMessages] = useState<
    { sender: string; text: string; time: string }[]
  >([
    {
      sender: 'IA Guide',
      text: t(
        'social.club_event.welcome_chat',
        "Bienvenue dans l'événement ! N'hésitez pas à poser vos questions ici.",
      ),
      time: t('social.club_event.system', 'Système'),
    },
  ]);
  const [newMessage, setNewMessage] = useState('');

  const fetchEventData = useCallback(async () => {
    if (!eventId || !id) return;
    try {
      const eventData = await socialService.getClubEventDetails(Number(eventId));
      setEvent(eventData);
      setIsParticipating(!!eventData.is_participant);
      setParticipantsCount(eventData.participants_count || 0);

      const clubData = await socialService.getClubDetails(Number(id));
      setClubName(clubData.name);
    } catch (err) {
      console.error('Erreur de récupération :', err);
      useToastStore
        .getState()
        .addToast(
          t('social.club_event.fetch_error', "Impossible de récupérer l'événement."),
          'error',
        );
    }
  }, [id, eventId, t]);

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      if (isMounted) {
        await fetchEventData();
      }
    };
    load();
    return () => {
      isMounted = false;
    };
  }, [fetchEventData]);

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
      const response = await socialService.toggleEventParticipation(Number(eventId));
      setIsParticipating(response.status === 'joined');
      setParticipantsCount(response.participants_count);
      useToastStore
        .getState()
        .addToast(
          response.status === 'joined'
            ? t('social.club_event.registered_success', 'Votre inscription a été enregistrée !')
            : t(
                'social.club_event.unregistered_success',
                'Vous ne participez plus à cet événement.',
              ),
          response.status === 'joined' ? 'success' : 'info',
        );
    } catch (err) {
      const error = err as { error?: string; message?: string };
      useToastStore
        .getState()
        .addToast(
          error.error ||
            t('social.club_event.action_error', 'Action impossible. Êtes-vous membre du club ?'),
          'error',
        );
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    setChatMessages((prev) => [
      ...prev,
      {
        sender: t('social.club_event.me', 'Moi'),
        text: newMessage,
        time: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
    setNewMessage('');
  };

  if (!event) {
    return (
      <div className="min-h-screen animate-pulse bg-[#0B0C10] p-20 text-center font-black uppercase tracking-[0.3em] text-[#F4F1E8]">
        {t('social.club_event.details_loading', "Chargement des détails de l'événement...")}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0C10] px-6 py-12 pt-20 text-[#F4F1E8]">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Back Link */}
        <Link
          to={`/clubs/${id}/`}
          className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:text-[#E8442B]"
        >
          <ChevronLeft className="w-4 h-4" />{' '}
          {t('social.club_event.back_to_club', 'Retour au club : {{name}}', { name: clubName })}
        </Link>

        {/* Hero Section */}
        <section className="relative flex flex-col items-start justify-between gap-8 overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 md:flex-row md:items-center md:p-12">
          <span
            className="font-manga pointer-events-none absolute -bottom-14 -right-4 text-[11rem] font-black italic leading-none text-[#E8442B]/[0.05]"
            aria-hidden
          >
            部
          </span>
          <div className="relative max-w-xl space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#E8442B]/25 bg-[#E8442B]/10 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[#E8442B]">
              <Calendar className="w-3.5 h-3.5" />{' '}
              {t('social.club_event.event_badge', 'Événement du Club')}
            </div>
            <h1 className="font-manga text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-5xl">
              {event.title}
            </h1>
            <p className="text-sm font-medium leading-relaxed text-[#8F94A5]">
              {event.description}
            </p>

            <div className="flex flex-wrap gap-4 text-xs font-bold uppercase tracking-wider text-[#8F94A5]">
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-[#FDB913]" />
                {new Date(event.event_date).toLocaleDateString('fr-FR', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </span>
              <span className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-[#E8442B]" />{' '}
                {t('social.club_event.voice_salon', "Salon Vocal de l'App")}
              </span>
              <span className="flex items-center gap-1.5">
                <Users className="w-4 h-4 text-[#FDB913]" />{' '}
                {t('social.club_event.registered_count', '{{count}} inscrits', {
                  count: participantsCount,
                })}
              </span>
            </div>
          </div>

          {/* Countdown / Status Box */}
          <div className="relative w-full space-y-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-6 text-center md:w-80">
            {isEventPast ? (
              <div className="space-y-2">
                <span className="inline-flex items-center gap-1 rounded-full bg-[#E8442B]/10 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[#E8442B]">
                  {t('social.club_event.past', 'Terminé')}
                </span>
                <p className="text-sm font-bold text-[#8F94A5]">
                  {t('social.club_event.past_desc', 'Cet événement est passé.')}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                <span className="inline-flex items-center gap-1 rounded-full bg-[#FDB913]/10 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[#FDB913]">
                  {t('social.club_event.upcoming', 'À venir')}
                </span>

                {/* Timer Grid */}
                <div className="grid grid-cols-4 gap-2">
                  <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] p-2.5">
                    <span className="font-manga block text-xl font-black italic text-[#FDB913]">
                      {timeLeft.days}
                    </span>
                    <span className="text-[8px] font-black uppercase text-[#8F94A5]">
                      {t('social.club_event.days', 'Jours')}
                    </span>
                  </div>
                  <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] p-2.5">
                    <span className="font-manga block text-xl font-black italic text-[#FDB913]">
                      {timeLeft.hours}
                    </span>
                    <span className="text-[8px] font-black uppercase text-[#8F94A5]">
                      {t('social.club_event.hours', 'Heures')}
                    </span>
                  </div>
                  <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] p-2.5">
                    <span className="font-manga block text-xl font-black italic text-[#FDB913]">
                      {timeLeft.minutes}
                    </span>
                    <span className="text-[8px] font-black uppercase text-[#8F94A5]">
                      {t('social.club_event.min', 'Min')}
                    </span>
                  </div>
                  <div className="rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] p-2.5">
                    <span className="font-manga block text-xl font-black italic text-[#FDB913]">
                      {timeLeft.seconds}
                    </span>
                    <span className="text-[8px] font-black uppercase text-[#8F94A5]">
                      {t('social.club_event.sec', 'Sec')}
                    </span>
                  </div>
                </div>

                <Button
                  onClick={handleToggleParticipation}
                  className={`flex w-full items-center justify-center gap-2 rounded-xl border-none py-4 font-manga font-black uppercase italic tracking-widest transition-colors cursor-pointer ${
                    isParticipating
                      ? '!bg-[#FDB913] !text-[#0B0C10] hover:!bg-[#e0a50f]'
                      : '!bg-[#E8442B] !text-[#F4F1E8] hover:!bg-[#c93a24]'
                  }`}
                >
                  {isParticipating ? (
                    <>
                      <CheckCircle className="w-4 h-4" />{' '}
                      {t('social.club_event.registered_badge', 'Inscrit(e) !')}
                    </>
                  ) : (
                    t('social.club_event.join_event', "Rejoindre l'événement")
                  )}
                </Button>
              </div>
            )}
          </div>
        </section>

        {/* Dual Panel - Info & Discussion */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Left / Center Column: Chat & Discussion */}
          <div className="flex h-[500px] flex-col space-y-6 overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 md:col-span-2">
            <h3 className="flex items-center gap-2 border-b border-[#F4F1E8]/10 pb-4 text-sm font-black uppercase tracking-wider text-[#8F94A5]">
              {t('social.club_event.chat_title', "Fil de discussion de l'événement")}
            </h3>

            {/* Messages */}
            <div className="flex-1 space-y-4 overflow-y-auto pr-2">
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex max-w-[80%] flex-col space-y-1 ${
                    msg.sender === t('social.club_event.me', 'Moi')
                      ? 'ml-auto items-end'
                      : 'mr-auto items-start'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-[#8F94A5]">{msg.sender}</span>
                    <span className="text-[9px] text-[#8F94A5]/70">{msg.time}</span>
                  </div>
                  <div
                    className={`rounded-2xl p-3.5 text-xs font-bold ${
                      msg.sender === t('social.club_event.me', 'Moi')
                        ? 'rounded-tr-none bg-[#E8442B] text-[#F4F1E8]'
                        : 'rounded-tl-none bg-[#0B0C10] text-[#F4F1E8]'
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            {/* Input Form */}
            <form
              onSubmit={handleSendMessage}
              className="flex gap-2 border-t border-[#F4F1E8]/10 pt-4"
            >
              <input
                type="text"
                aria-label={t('social.club_event.chat_aria', 'Votre message')}
                placeholder={t(
                  'social.club_event.chat_placeholder',
                  'Posez vos questions ou discutez du concept...',
                )}
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                className="flex-1 rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] p-4 text-xs font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
              />
              <button
                type="submit"
                className="flex items-center justify-center rounded-xl border-none bg-[#E8442B] p-4 text-[#F4F1E8] transition-colors hover:bg-[#c93a24] cursor-pointer"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </div>

          {/* Right Column: Info & Status */}
          <div className="space-y-6 rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6">
            <h3 className="flex items-center gap-2 border-b border-[#F4F1E8]/10 pb-4 text-sm font-black uppercase tracking-wider text-[#8F94A5]">
              {t('social.club_event.ai_stats', "Statistiques de l'IA")}
            </h3>

            <div className="space-y-4">
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
                <p className="mb-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  {t('social.club_event.expected_impact', 'Impact prévu')}
                </p>
                <p className="font-manga text-lg font-black italic text-[#FDB913]">+250 XP</p>
              </div>
              <div className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4">
                <p className="mb-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                  {t('social.club_event.vibe_detected', 'Vibe détectée')}
                </p>
                <p className="font-manga text-lg font-black italic text-[#E8442B]">
                  {t('social.club_event.vibe_value', 'Social / Débat')}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClubEventPage;
