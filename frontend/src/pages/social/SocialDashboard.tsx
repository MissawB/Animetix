import React from 'react';
import { Link } from 'react-router-dom';
import { UserMinus } from 'lucide-react';
import { useSocialDashboard } from '../../features/social/hooks/useSocialDashboard';
import { useTranslation } from 'react-i18next';
import { CardSkeleton } from '../../components/ui/Skeleton';
import { Friendship } from '../../types';
import { LabPage, LabHeader, LabPanel } from '../labs/components/shared/LabKit';

/** Sceaux et encres des modules du nexus — repris des pages déjà encrées. */
interface NexusLink {
  title: string;
  desc: string;
  glyph: string;
  ink: string;
  to: string;
}

/** Carte-lien papier du nexus : même langage de sceau que le hub labs
 *  (kanji encré à la couleur du module, filigrane discret, survol en or). */
const NexusLinkCard: React.FC<NexusLink> = ({ title, desc, glyph, ink, to }) => (
  <Link to={to} className="group block h-full no-underline">
    <article className="relative h-full overflow-hidden rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 transition-all duration-300 group-hover:-translate-y-1 group-hover:border-[#FDB913]/60">
      <span
        aria-hidden
        className="pointer-events-none absolute -bottom-5 -right-2 select-none text-[5.5rem] font-black leading-none text-[#F4F1E8]/[0.045] transition-colors duration-500 group-hover:text-[#FDB913]/[0.08]"
      >
        {glyph}
      </span>
      <span
        className="select-none text-2xl font-bold leading-none"
        style={{ color: ink }}
        aria-hidden
      >
        {glyph}
      </span>
      <h4 className="font-manga mt-6 text-lg font-black uppercase italic tracking-tight text-[#F4F1E8]">
        {title}
      </h4>
      <p className="mt-2 text-xs leading-relaxed text-[#8F94A5]">{desc}</p>
    </article>
  </Link>
);

const SocialDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { data, isLoading, isError, toggleFollow } = useSocialDashboard();

  if (isLoading)
    return (
      <div className="min-h-screen w-full bg-[#0B0C10] pt-20">
        <div className="mx-auto max-w-7xl space-y-12 px-4 py-12 sm:px-6">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </div>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
            <CardSkeleton />
            <CardSkeleton />
          </div>
        </div>
      </div>
    );

  if (isError || !data)
    return (
      <div className="flex min-h-screen w-full items-center justify-center bg-[#0B0C10] text-center">
        <p className="font-manga text-2xl font-black uppercase italic text-[#E8442B]">
          {t('common.error')}
        </p>
      </div>
    );

  return (
    <LabPage>
      <LabHeader
        glyph="絆"
        code="Registre · Communauté"
        title="Nexus"
        accent="Social"
        lede="Vos instruments cognitifs et le registre de vos liens — abonnements, abonnés, clubs."
      />

      {/* Nexus Cognitive Suite */}
      <section className="mb-12">
        <div className="mb-8 flex items-center gap-3">
          <span className="h-4 w-1 flex-none bg-[#E8442B]" aria-hidden />
          <h3 className="font-manga text-sm font-black uppercase italic tracking-wide text-[#F4F1E8]">
            Nexus Cognitive Suite
          </h3>
          <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden />
        </div>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
          <NexusLinkCard
            title="Archetype Nexus"
            desc={t('social.dashboard.nexus_desc', 'Votre profil neuronal.')}
            glyph="型"
            ink="#5D7FD3"
            to="/social/archetype-nexus/"
          />
          <NexusLinkCard
            title="AI Debate Arena"
            desc={t('social.dashboard.debate_desc', 'Duels sémantiques.')}
            glyph="論"
            ink="#E8442B"
            to="/social/debate-arena/"
          />
          <NexusLinkCard
            title="Ma Collection"
            desc={t('social.dashboard.collection_desc', 'Fusions & Favoris.')}
            glyph="蔵"
            ink="#FDB913"
            to="/social/collection/"
          />
          <NexusLinkCard
            title="Clubs"
            desc={t('social.dashboard.clubs_desc', 'Communautés actives.')}
            glyph="部"
            ink="#F4F1E8"
            to="/clubs/"
          />
          <NexusLinkCard
            title="Neuro-Memory"
            desc={t('social.dashboard.neuro_desc', 'Gérez votre empreinte.')}
            glyph="憶"
            ink="#FDB913"
            to="/social/neuro-memory/"
          />
        </div>
      </section>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        {/* Abonnements */}
        <LabPanel title={t('social.dashboard.following_title')}>
          <div className="space-y-4">
            {data.following.map((f: Friendship) => (
              <div
                key={f.id}
                className="flex items-center justify-between gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4 transition-colors hover:border-[#FDB913]/40"
              >
                <Link
                  to={`/profile/${f.username}/`}
                  className="flex min-w-0 items-center gap-4 no-underline"
                >
                  <span className="flex h-11 w-11 flex-none items-center justify-center rounded-full bg-[#FDB913] font-black italic text-[#0B0C10]">
                    {f.username[0].toUpperCase()}
                  </span>
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-bold text-[#F4F1E8]">
                      {f.username}
                    </span>
                    <span className="block text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                      {t('social.profile.level', { level: f.level })}
                    </span>
                  </span>
                </Link>
                <button
                  onClick={() => toggleFollow(f.to_user)}
                  className="inline-flex flex-none cursor-pointer items-center gap-2 rounded-full border border-[#F4F1E8]/15 bg-transparent px-4 py-2 text-[10px] font-black uppercase tracking-widest text-[#8F94A5] transition-colors hover:border-[#E8442B] hover:text-[#E8442B] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                >
                  <UserMinus className="h-3.5 w-3.5" aria-hidden="true" />{' '}
                  {t('social.dashboard.unfollow')}
                </button>
              </div>
            ))}
            {data.following.length === 0 && (
              <p className="py-8 text-center text-sm italic text-[#8F94A5]">
                {t('social.dashboard.no_following')}
              </p>
            )}
          </div>
        </LabPanel>

        {/* Abonnés */}
        <LabPanel title={t('social.dashboard.followers_title')}>
          <div className="space-y-4">
            {data.followers.map((f: Friendship) => (
              <div
                key={f.id}
                className="flex items-center gap-4 rounded-2xl border border-[#F4F1E8]/10 bg-[#0B0C10] p-4"
              >
                <span className="flex h-11 w-11 flex-none items-center justify-center rounded-full bg-[#F4F1E8] font-black italic text-[#0B0C10]">
                  {f.username[0].toUpperCase()}
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-sm font-bold text-[#F4F1E8]">
                    {f.username}
                  </span>
                  <span className="block text-[10px] font-black uppercase tracking-widest text-[#8F94A5]">
                    {t('social.profile.level', { level: f.level })}
                  </span>
                </span>
              </div>
            ))}
            {data.followers.length === 0 && (
              <p className="py-8 text-center text-sm italic text-[#8F94A5]">
                {t('social.dashboard.no_followers')}
              </p>
            )}
          </div>
        </LabPanel>
      </div>
    </LabPage>
  );
};

export default SocialDashboard;
