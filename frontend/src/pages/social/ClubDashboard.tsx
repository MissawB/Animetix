import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import {
  ChevronLeft,
  Users,
  Settings,
  Bell,
  Info,
  Calendar,
  Plus,
  Clock,
  FileText,
} from 'lucide-react';
import ClubChat from '../../features/social/components/ClubChat';
import { socialService } from '../../features/social/services/socialService';
import { useToastStore } from '../../store/toastStore';
import { useClub } from '../../features/social/hooks/useClub';
import { Modal } from '../../components/ui/Modal';
import { useTranslation } from 'react-i18next';

interface Member {
  id: string;
  username: string;
  avatar?: string;
  role: 'admin' | 'moderator' | 'member';
  status: 'online' | 'offline';
}

const ClubDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const clubId = Number(id);
  const { club, isLoadingClub, events } = useClub(clubId);
  const queryClient = useQueryClient();

  const [activeTab, setActiveTab] = useState<'chat' | 'events'>('chat');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newEventTitle, setNewEventTitle] = useState('');
  const [newEventDescription, setNewEventDescription] = useState('');
  const [newEventDate, setNewEventDate] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Simulation des membres (Technical Debt: Should come from an API)
  const members: Member[] = [
    { id: '1', username: 'Bahma', role: 'admin', status: 'online' },
    { id: '2', username: 'Alice', role: 'moderator', status: 'online' },
    { id: '3', username: 'Bob', role: 'member', status: 'offline' },
    { id: '4', username: 'Charlie', role: 'member', status: 'online' },
  ];

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEventTitle || !newEventDate || !newEventDescription) {
      useToastStore
        .getState()
        .addToast(t('social.club.fill_fields', 'Veuillez remplir tous les champs.'), 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      await socialService.createClubEvent({
        club: clubId,
        title: newEventTitle,
        description: newEventDescription,
        event_date: newEventDate,
      });
      useToastStore
        .getState()
        .addToast(t('social.club.event_created', 'Événement créé avec succès !'), 'success');
      setNewEventTitle('');
      setNewEventDescription('');
      setNewEventDate('');
      setShowCreateModal(false);
      // L'événement est créé via l'API ; on invalide la query events de useClub
      // (même clé) pour rafraîchir la liste sans recharger toute la page.
      queryClient.invalidateQueries({ queryKey: ['club', clubId, 'events'] });
    } catch (err) {
      const error = err as { error?: string; message?: string };
      console.error(error);
      useToastStore
        .getState()
        .addToast(
          error?.error ||
            error?.message ||
            t('social.club.create_error', "Erreur lors de la création de l'événement."),
          'error',
        );
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoadingClub) {
    return (
      <div className="min-h-screen animate-pulse bg-[#0B0C10] p-20 text-center font-black uppercase tracking-widest text-[#F4F1E8]">
        {t('social.club.syncing', 'Synchronisation avec le club...')}
      </div>
    );
  }

  const clubName = club?.name || t('social.club.loading', 'Chargement...');
  const description = club?.description;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-[#0B0C10] text-[#F4F1E8]">
      {/* Header */}
      <div className="flex flex-none items-center justify-between border-b border-[#F4F1E8]/10 p-4 lg:p-6">
        <div className="flex items-center gap-4">
          <Link
            to="/social/discovery/"
            className="rounded-xl p-2 text-[#8F94A5] transition-colors hover:bg-[#F4F1E8]/5 hover:text-[#F4F1E8]"
          >
            <ChevronLeft className="w-6 h-6" />
          </Link>
          <div>
            <h1 className="font-manga text-xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8]">
              {clubName}
            </h1>
            <div className="mt-1 flex items-center gap-2 text-[#8F94A5]">
              <Users className="w-3 h-3" />
              <span className="text-[10px] font-bold uppercase tracking-widest">
                {t('social.club.active_members', '{{count}} Membres actifs', {
                  count: members.length,
                })}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Tabs Selector */}
          <div className="mr-4 flex rounded-xl border border-[#F4F1E8]/10 bg-[#0F1016] p-1">
            <button
              onClick={() => setActiveTab('chat')}
              className={`rounded-lg px-4 py-2 text-xs font-black uppercase tracking-wider transition-colors ${
                activeTab === 'chat'
                  ? 'bg-[#E8442B] text-[#F4F1E8]'
                  : 'text-[#8F94A5] hover:text-[#F4F1E8]'
              }`}
            >
              {t('social.club.discussion', 'Discussion')}
            </button>
            <button
              onClick={() => setActiveTab('events')}
              className={`rounded-lg px-4 py-2 text-xs font-black uppercase tracking-wider transition-colors ${
                activeTab === 'events'
                  ? 'bg-[#E8442B] text-[#F4F1E8]'
                  : 'text-[#8F94A5] hover:text-[#F4F1E8]'
              }`}
            >
              {t('social.club.events', 'Événements ({{count}})', { count: events.length })}
            </button>
          </div>

          <button className="rounded-xl p-2 text-[#8F94A5] transition-colors hover:bg-[#F4F1E8]/5 hover:text-[#F4F1E8]">
            <Bell className="w-5 h-5" />
          </button>
          <button className="rounded-xl p-2 text-[#8F94A5] transition-colors hover:bg-[#F4F1E8]/5 hover:text-[#F4F1E8]">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative flex flex-grow overflow-hidden">
        {/* Active View: Chat */}
        {activeTab === 'chat' && (
          <div className="flex-1 overflow-hidden p-4 lg:p-6">
            <ClubChat clubId={id || ''} clubName={clubName} />
          </div>
        )}

        {/* Active View: Events */}
        {activeTab === 'events' && (
          <div className="flex-grow space-y-6 overflow-y-auto p-6">
            <div className="mx-auto max-w-4xl space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-manga text-2xl font-black uppercase italic tracking-tight text-[#F4F1E8]">
                    {t('social.club.scheduled_events', 'Événements programmés')}
                  </h2>
                  <p className="mt-1 text-xs font-bold uppercase tracking-wider text-[#8F94A5]">
                    {t(
                      'social.club.events_desc',
                      'Découvrez et rejoignez les activités organisées par le club.',
                    )}
                  </p>
                </div>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="group relative flex items-center gap-2 rounded-xl border-none bg-[#E8442B] px-5 py-3 font-manga text-xs font-black uppercase italic tracking-widest text-[#F4F1E8] transition-colors hover:bg-[#c93a24] cursor-pointer"
                >
                  <Plus className="w-4 h-4" /> {t('social.club.create_event', 'Créer un événement')}
                </button>
              </div>

              {events.length === 0 ? (
                <div className="space-y-4 rounded-2xl border border-dashed border-[#F4F1E8]/15 p-16 text-center">
                  <Calendar className="mx-auto h-12 w-12 text-[#8F94A5]/40" />
                  <p className="font-bold text-[#8F94A5]">
                    {t(
                      'social.club.no_events',
                      "Aucun événement n'est actuellement programmé pour ce club.",
                    )}
                  </p>
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="cursor-pointer border-none bg-transparent text-xs font-black uppercase tracking-widest text-[#E8442B] hover:underline"
                  >
                    {t(
                      'social.club.launch_first_event',
                      'Lancez le premier événement maintenant !',
                    )}
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {events.map((event) => (
                    <Link
                      key={event.id}
                      to={`/clubs/${id}/events/${event.id}`}
                      className="group flex flex-col justify-between rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 text-[#F4F1E8] no-underline transition-colors hover:border-[#E8442B]/40"
                    >
                      <div className="space-y-4">
                        <div className="flex items-start justify-between">
                          <span className="rounded-xl bg-[#E8442B]/10 p-3 text-[#E8442B] transition-transform group-hover:scale-110">
                            <Calendar className="w-6 h-6" />
                          </span>
                          <span className="flex items-center gap-1 rounded-full bg-[#F4F1E8]/5 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                            <Clock className="w-3 h-3" />
                            {new Date(event.event_date).toLocaleDateString('fr-FR', {
                              day: 'numeric',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                        <div className="space-y-2">
                          <h3 className="font-manga line-clamp-1 text-lg font-black uppercase italic tracking-tight text-[#F4F1E8] transition-colors group-hover:text-[#E8442B]">
                            {event.title}
                          </h3>
                          <p className="line-clamp-3 text-xs leading-relaxed text-[#8F94A5]">
                            {event.description}
                          </p>
                        </div>
                      </div>
                      <div className="mt-4 flex items-center justify-between border-t border-[#F4F1E8]/10 pt-4 text-xs font-black uppercase tracking-widest text-[#E8442B]">
                        <span>{t('social.club.view_details', 'Voir les détails')}</span>
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
        <div className="hidden w-80 flex-col overflow-hidden border-l border-[#F4F1E8]/10 bg-[#0F1016] lg:flex">
          <div className="space-y-8 overflow-y-auto p-6">
            {/* Club Info */}
            <div className="space-y-3">
              <h3 className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.2em] text-[#8F94A5]">
                <Info className="w-3 h-3" /> About Club
              </h3>
              <p className="text-sm leading-relaxed text-[#8F94A5]">
                {description ||
                  t('social.club.no_description', 'Pas de description disponible pour ce club.')}
              </p>
            </div>

            {/* Member List */}
            <div className="space-y-4">
              <h3 className="flex items-center gap-2 text-xs font-black uppercase tracking-[0.2em] text-[#8F94A5]">
                <Users className="w-3 h-3" />{' '}
                {t('social.club.members_online', 'Membres — {{count}} en ligne', {
                  count: members.filter((m) => m.status === 'online').length,
                })}
              </h3>
              <div className="space-y-2">
                {members.map((member) => (
                  <div
                    key={member.id}
                    className="group flex items-center justify-between rounded-xl p-2 transition-colors hover:bg-[#F4F1E8]/5"
                  >
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#E8442B]/15 text-xs font-bold text-[#E8442B]">
                          {member.username[0]}
                        </div>
                        <div
                          className={`absolute -bottom-1 -right-1 h-3 w-3 rounded-full border-2 border-[#0F1016] ${
                            member.status === 'online' ? 'bg-[#FDB913]' : 'bg-[#8F94A5]'
                          }`}
                        />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-[#F4F1E8]">{member.username}</p>
                        <p
                          className={`text-[9px] font-black uppercase tracking-widest ${
                            member.role === 'admin'
                              ? 'text-[#E8442B]'
                              : member.role === 'moderator'
                                ? 'text-[#FDB913]'
                                : 'text-[#8F94A5]'
                          }`}
                        >
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
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title={t('social.club.plan_event', 'Planifier un événement')}
        size="md"
        contentClassName="bg-[#0F1016] border border-[#F4F1E8]/10 rounded-2xl shadow-2xl"
      >
        <form onSubmit={handleCreateEvent} className="space-y-6">
          <div className="space-y-2">
            <label
              htmlFor="event-title"
              className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-[#8F94A5]"
            >
              <FileText className="w-3 h-3" />{' '}
              {t('social.club.event_title', "Titre de l'événement")}
            </label>
            <input
              id="event-title"
              type="text"
              required
              aria-label={t('social.club.event_title', "Titre de l'événement")}
              placeholder={t(
                'social.club.event_title_placeholder',
                'Ex : Soirée analyse Scan Shonen Jump 125',
              )}
              value={newEventTitle}
              onChange={(e) => setNewEventTitle(e.target.value)}
              className="w-full rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] p-4 text-sm font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="event-description"
              className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-[#8F94A5]"
            >
              <Info className="w-3 h-3" />{' '}
              {t('social.club.event_desc_label', "Description de l'activité")}
            </label>
            <textarea
              id="event-description"
              required
              rows={4}
              aria-label={t('social.club.event_desc_label', "Description de l'activité")}
              placeholder={t(
                'social.club.event_desc_placeholder',
                'Expliquez le concept, le déroulement, ou les prérequis pour cet événement...',
              )}
              value={newEventDescription}
              onChange={(e) => setNewEventDescription(e.target.value)}
              className="w-full resize-none rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] p-4 text-sm font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
            />
          </div>

          <div className="space-y-2">
            <label
              htmlFor="event-date"
              className="flex items-center gap-1.5 text-[10px] font-black uppercase tracking-wider text-[#8F94A5]"
            >
              <Clock className="w-3 h-3" /> {t('social.club.event_date', 'Date et Heure')}
            </label>
            <input
              id="event-date"
              type="datetime-local"
              required
              aria-label={t('social.club.event_date', 'Date et Heure')}
              value={newEventDate}
              onChange={(e) => setNewEventDate(e.target.value)}
              className="w-full rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] p-4 text-sm font-medium text-[#F4F1E8] outline-none transition-colors focus:border-[#FDB913]"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-xl border-none bg-[#E8442B] py-4 font-manga text-xs font-black uppercase italic tracking-widest text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:opacity-50 cursor-pointer"
          >
            {isSubmitting
              ? t('social.club.creating', 'Création en cours...')
              : t('social.club.confirm_event', "Confirmer l'événement")}
          </button>
        </form>
      </Modal>
    </div>
  );
};

export default ClubDashboard;
