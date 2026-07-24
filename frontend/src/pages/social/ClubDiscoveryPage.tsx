import React, { useState } from 'react';
import { Users, Search, Plus, Shield, Layout, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '../../utils/apiClient';
import { socialService } from '../../features/social/services/socialService';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { queryClient } from '../../utils/queryClient';
import { Modal } from '../../components/ui/Modal';
import { useTranslation } from 'react-i18next';

interface Club {
  id: string;
  name: string;
  description: string;
  theme: string;
  member_count: number;
}

const ClubDiscoveryPage: React.FC = () => {
  const { t } = useTranslation();
  const [filter, setFilter] = useState('');
  const [selectedTheme, setSelectedTheme] = useState('All');
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Form State
  const [newClub, setNewClub] = useState({
    name: '',
    description: '',
    theme: 'General',
    is_private: false,
  });

  const { data: clubs = [] } = useQuery<Club[]>({
    queryKey: ['clubs-list'],
    queryFn: async () => {
      const data = await apiClient('/api/v1/clubs/');
      // L'endpoint est paginé DRF : la liste est dans `results`.
      return Array.isArray(data) ? data : (data?.results ?? []);
    },
  });

  const createMutation = useMutation({
    mutationFn: socialService.createClub,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clubs-list'] });
      setIsModalOpen(false);
      setNewClub({ name: '', description: '', theme: 'General', is_private: false });
    },
  });

  // Garde contre un cache persisté (IndexedDB, 24h) datant d'avant la
  // normalisation : il peut encore contenir l'objet paginé DRF brut.
  const filteredClubs = (Array.isArray(clubs) ? clubs : []).filter(
    (club) =>
      (selectedTheme === 'All' || club.theme === selectedTheme) &&
      (club.name.toLowerCase().includes(filter.toLowerCase()) ||
        club.description.toLowerCase().includes(filter.toLowerCase())),
  );

  const themes = ['All', 'Shonen', 'Shojo', 'Seinen', 'Sci-Fi', 'Slice of Life', 'General'];

  return (
    <div className="min-h-screen w-full bg-[#0B0C10] px-4 py-12 pt-20 text-[#F4F1E8] sm:px-6">
      <div className="mx-auto max-w-7xl">
        <header className="relative mb-12">
          <div
            className="explore-halftone pointer-events-none absolute -inset-x-6 -top-12 h-48"
            aria-hidden
          />
          <div className="relative flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <div className="flex items-center gap-3">
                <span className="explore-stamp -rotate-2" aria-hidden>
                  部
                </span>
                <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
                  Nexus social · Cercles
                </span>
              </div>
              <h1 className="font-manga mt-4 text-4xl font-black uppercase italic leading-none tracking-tighter text-[#F4F1E8] md:text-6xl">
                Club <span className="text-[#E8442B]">Discovery</span>
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-relaxed text-[#8F94A5]">
                {t('social.discovery.subtitle', 'Rejoignez une communauté ou créez la vôtre.')}
              </p>
            </div>
            <button
              onClick={() => setIsModalOpen(true)}
              className="inline-flex flex-none items-center justify-center gap-2 rounded-xl border-none bg-[#E8442B] px-8 py-4 font-manga text-base font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913] cursor-pointer"
            >
              <Plus className="w-5 h-5" /> {t('social.discovery.create_club', 'Créer un Club')}
            </button>
          </div>
          <span className="relative mt-8 block h-px bg-[#F4F1E8]/10" aria-hidden />
        </header>

        <Modal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          title={
            <span className="text-2xl font-black italic font-manga uppercase text-[#F4F1E8]">
              {t('social.discovery.new_nexus', 'Nouveau Nexus Social')}
            </span>
          }
          size="md"
          contentClassName="bg-[#0F1016] border border-[#F4F1E8]/10 rounded-2xl shadow-2xl"
        >
          <form
            className="space-y-8"
            onSubmit={(e) => {
              e.preventDefault();
              createMutation.mutate(newClub);
            }}
          >
            <div className="space-y-2">
              <label
                htmlFor="club-name"
                className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5] ml-1"
              >
                {t('social.discovery.club_name', 'Nom du Club')}
              </label>
              <input
                id="club-name"
                required
                type="text"
                aria-label={t('social.discovery.club_name', 'Nom du Club')}
                className="w-full rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] px-6 py-4 text-sm font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
                placeholder={t(
                  'social.discovery.club_name_placeholder',
                  'ex: Les Héritiers du Lore',
                )}
                value={newClub.name}
                onChange={(e) => setNewClub({ ...newClub, name: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-2">
                <label
                  htmlFor="club-theme"
                  className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5] ml-1"
                >
                  {t('social.discovery.main_theme', 'Thème Principal')}
                </label>
                <select
                  id="club-theme"
                  className="w-full appearance-none rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] px-6 py-4 text-sm font-medium text-[#F4F1E8] outline-none transition-colors focus:border-[#FDB913]"
                  value={newClub.theme}
                  onChange={(e) => setNewClub({ ...newClub, theme: e.target.value })}
                >
                  {themes
                    .filter((t) => t !== 'All')
                    .map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                </select>
              </div>
              <div className="space-y-2">
                <span className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5] ml-1 block">
                  {t('social.discovery.confidentiality', 'Confidentialité')}
                </span>
                <div className="flex rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] p-1">
                  <button
                    type="button"
                    onClick={() => setNewClub({ ...newClub, is_private: false })}
                    className={`flex-1 rounded-lg py-3 text-[10px] font-black uppercase transition-colors ${!newClub.is_private ? 'bg-[#F4F1E8] text-[#0B0C10]' : 'text-[#8F94A5]'}`}
                  >
                    {t('social.discovery.public', 'Public')}
                  </button>
                  <button
                    type="button"
                    onClick={() => setNewClub({ ...newClub, is_private: true })}
                    className={`flex-1 rounded-lg py-3 text-[10px] font-black uppercase transition-colors ${newClub.is_private ? 'bg-[#E8442B] text-[#F4F1E8]' : 'text-[#8F94A5]'}`}
                  >
                    {t('social.discovery.private', 'Privé')}
                  </button>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              <label
                htmlFor="club-description"
                className="text-[10px] font-black uppercase tracking-widest text-[#8F94A5] ml-1"
              >
                {t('social.discovery.description', 'Description (Lore)')}
              </label>
              <textarea
                id="club-description"
                required
                rows={4}
                aria-label={t('social.discovery.description', 'Description (Lore)')}
                className="w-full resize-none rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] px-6 py-4 text-sm font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
                placeholder={t(
                  'social.discovery.description_placeholder',
                  "Décrivez l'objectif du club...",
                )}
                value={newClub.description}
                onChange={(e) => setNewClub({ ...newClub, description: e.target.value })}
              />
            </div>
            <Button
              type="submit"
              disabled={createMutation.isPending}
              className="w-full rounded-xl !bg-[#E8442B] py-5 font-manga text-xs font-black uppercase italic tracking-widest !text-[#F4F1E8] transition-colors hover:!bg-[#c93a24] disabled:opacity-50"
            >
              {createMutation.isPending
                ? t('social.discovery.creating', 'Création du Nexus...')
                : t('social.discovery.submit', 'Fonder le Club →')}
            </Button>
          </form>
        </Modal>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
          {/* Filters */}
          <div className="lg:col-span-1 space-y-6">
            <section className="h-fit rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8">
              <h3 className="mb-6 flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                <Search className="w-4 h-4" /> Nexus Filter
              </h3>
              <div className="space-y-8">
                <div className="space-y-2">
                  <label htmlFor="nexus-search" className="sr-only">
                    {t('social.discovery.search_club', 'Rechercher un club')}
                  </label>
                  <input
                    id="nexus-search"
                    type="text"
                    aria-label={t('social.discovery.search_club', 'Rechercher un club')}
                    placeholder={t(
                      'social.discovery.search_club_placeholder',
                      'Rechercher un club...',
                    )}
                    className="w-full rounded-xl border border-[#F4F1E8]/15 bg-[#0B0C10] px-4 py-4 text-xs font-medium text-[#F4F1E8] outline-none transition-colors placeholder:text-[#8F94A5]/60 focus:border-[#FDB913]"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                  />
                </div>
                <div className="space-y-4">
                  <span className="block text-[8px] font-black uppercase tracking-[0.2em] text-[#8F94A5]">
                    {t('social.discovery.thematic_sector', 'Secteur Thématique')}
                  </span>
                  <div className="flex flex-col gap-2">
                    {themes.map((theme) => (
                      <button
                        key={theme}
                        onClick={() => setSelectedTheme(theme)}
                        className={`rounded-xl px-4 py-3 text-left text-[10px] font-black uppercase tracking-widest transition-colors ${
                          selectedTheme === theme
                            ? 'bg-[#E8442B] text-[#F4F1E8]'
                            : 'bg-[#F4F1E8]/5 text-[#8F94A5] hover:bg-[#F4F1E8]/10'
                        }`}
                      >
                        {theme}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </section>

            <section className="rounded-2xl border border-[#E8442B]/25 bg-[#E8442B]/[0.05] p-6 sm:p-8 text-[#E8442B]/70">
              <Shield className="mb-4 h-10 w-10 opacity-40" />
              <p className="text-[10px] font-bold uppercase italic leading-relaxed">
                {t(
                  'social.discovery.private_hint',
                  'Les clubs privés nécessitent une invitation ou une validation par un officier du cercle.',
                )}
              </p>
            </section>
          </div>

          {/* Club Grid */}
          <div className="lg:col-span-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {filteredClubs.map((club) => (
                <div
                  key={club.id}
                  className="group relative overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-8 transition-colors hover:border-[#F4F1E8]/20"
                >
                  {/* Decor */}
                  <Layout className="absolute -right-8 -bottom-8 h-40 w-40 rotate-12 text-[#F4F1E8] opacity-[0.03] transition-opacity group-hover:opacity-[0.06]" />

                  <div className="mb-6 flex items-start justify-between">
                    <div className="rounded-xl bg-[#E8442B]/10 p-4 text-[#E8442B] transition-transform group-hover:scale-110">
                      <Users className="w-8 h-8" />
                    </div>
                    <Badge
                      variant="neutral"
                      className="!bg-[#F4F1E8]/5 !border-[#F4F1E8]/10 text-[8px] font-black uppercase tracking-widest !text-[#8F94A5]"
                    >
                      {club.theme}
                    </Badge>
                  </div>
                  <h2 className="font-manga mb-3 text-2xl font-black uppercase italic leading-none tracking-tight text-[#F4F1E8] transition-colors group-hover:text-[#E8442B]">
                    {club.name}
                  </h2>
                  <p className="mb-8 line-clamp-2 text-xs font-medium uppercase italic tracking-wide text-[#8F94A5]">
                    "{club.description}"
                  </p>
                  <div className="mt-auto flex items-center justify-between border-t border-[#F4F1E8]/10 pt-6">
                    <span className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                      <Sparkles className="h-3 w-3 text-[#FDB913]" />{' '}
                      {t('social.discovery.member_count', '{{count}} Membres', {
                        count: club.member_count,
                      })}
                    </span>
                    <Link
                      to={`/clubs/${club.id}`}
                      className="rounded-xl bg-[#F4F1E8] px-8 py-3 text-[10px] font-black uppercase tracking-widest text-[#0B0C10] no-underline transition-colors hover:bg-[#FDB913]"
                    >
                      {t('social.discovery.join', 'Rejoindre')}
                    </Link>
                  </div>
                </div>
              ))}
            </div>

            {filteredClubs.length === 0 && (
              <div className="rounded-2xl border border-dashed border-[#F4F1E8]/15 py-32 text-center">
                <Users className="mx-auto mb-6 h-24 w-24 text-[#8F94A5]/30" />
                <p className="font-manga text-2xl font-black uppercase italic text-[#F4F1E8]/40">
                  {t('social.discovery.no_nexus', 'Aucun Nexus actif dans ce secteur')}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ClubDiscoveryPage;
