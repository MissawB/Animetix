import React, { useId, useState } from 'react';
import { Search } from 'lucide-react';
import { useAuthStore } from '../../../store/authStore';
import { Button } from '../../../components/ui/Button';
import { Modal } from '../../../components/ui/Modal';
import { useTrackerLinks } from './useTrackerLinks';
import type { TrackerCandidate, TrackerName } from './trackerLinkService';

const TRACKER_LABELS: Record<TrackerName, string> = {
  anilist: 'AniList',
  myanimelist: 'MyAnimeList',
};

/** Encart de la fiche œuvre : confirme ou corrige à quelle entrée distante
 *  (AniList / MyAnimeList) ce manga est lié. Ne s'affiche jamais pour un
 *  visiteur anonyme, ni si l'utilisateur n'a connecté aucun tracker — inciter
 *  à connecter un compte n'est pas le rôle de cette fiche. */
export const TrackerLinkCard: React.FC<{ mediaId: string }> = ({ mediaId }) => {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { links, connected, isLoading, confirm, unlink, search } = useTrackerLinks(
    mediaId,
    isAuthenticated,
  );
  const [searchTracker, setSearchTracker] = useState<TrackerName | null>(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<TrackerCandidate[]>([]);
  const searchInputId = useId();

  if (!isAuthenticated) return null;
  if (isLoading) return null;
  // `connected` vide = l'utilisateur n'a lié aucun compte tracker. Un `links`
  // non vide ne suffit PAS à afficher l'encart dans ce cas : le backend peut
  // renvoyer une liaison confirmée dont la connexion source a depuis été
  // supprimée (déconnexion du compte AniList/MAL sans purge de la liaison
  // côté serveur) — sans ce garde-fou, l'encart afficherait une progression
  // et un bouton « Délier » pour un compte qui n'existe plus.
  if (connected.length === 0) return null;

  // Même raison, tracker par tracker : avec deux comptes connectés dont un est
  // déconnecté ensuite, ses liaisons restent en base (voulu — elles redeviennent
  // actives à la reconnexion) mais ne doivent plus s'afficher ici, sans quoi la
  // fiche œuvre montre une progression et un bouton « Délier » pour un compte
  // que le panneau profil, lui, n'affiche plus.
  const visibleLinks = links.filter((link) => connected.includes(link.tracker));
  const unmatched = connected.filter(
    (tracker) => !visibleLinks.some((link) => link.tracker === tracker),
  );

  const openSearch = (tracker: TrackerName) => {
    setSearchTracker(tracker);
    setQuery('');
    setResults([]);
  };

  const closeSearch = () => setSearchTracker(null);

  const handleSearch = async () => {
    if (!searchTracker || !query.trim()) return;
    const response = await search.mutateAsync({ tracker: searchTracker, query });
    setResults(response.results);
  };

  const handlePick = async (candidate: TrackerCandidate) => {
    if (!searchTracker) return;
    // Le titre du candidat part avec la confirmation : c'est le seul moment où
    // on l'a, et sans lui la liaison corrigée s'affiche sans nom d'œuvre.
    await confirm.mutateAsync({
      tracker: searchTracker,
      remoteId: candidate.remote_id,
      remoteTitle: candidate.title,
    });
    closeSearch();
  };

  return (
    <section>
      <h3 className="mb-6 flex items-center gap-4 font-manga text-xl font-black uppercase italic tracking-wide text-[#F4F1E8] md:text-2xl">
        <span className="h-6 w-1.5 flex-none bg-[#E8442B]" aria-hidden="true" />
        Trackers
        <span className="h-px flex-1 bg-[#F4F1E8]/10" aria-hidden="true" />
      </h3>

      <div className="space-y-2">
        {visibleLinks.map((link) => (
          <div
            key={link.tracker}
            className="flex items-center justify-between gap-3 rounded-2xl border border-white/5 bg-gray-900/50 p-4 transition-colors hover:border-white/10"
          >
            <div>
              <span className="mr-3 text-[10px] font-black uppercase opacity-30">
                {TRACKER_LABELS[link.tracker]}
              </span>
              <span className="text-sm font-bold italic">{link.remote_title}</span>
              {link.status === 'confirmed' && link.remote_progress != null && (
                <span className="ml-3 text-xs opacity-60">
                  {link.remote_progress} chapitres suivis
                </span>
              )}
            </div>
            {link.status === 'suggested' ? (
              <Button
                size="sm"
                onClick={() =>
                  confirm.mutate({
                    tracker: link.tracker,
                    remoteId: link.remote_id,
                    remoteTitle: link.remote_title,
                  })
                }
              >
                Lier
              </Button>
            ) : (
              <Button size="sm" variant="outline" onClick={() => unlink.mutate(link.tracker)}>
                Délier
              </Button>
            )}
          </div>
        ))}

        {unmatched.map((tracker) => (
          <div
            key={tracker}
            className="flex items-center justify-between gap-3 rounded-2xl border border-white/5 bg-gray-900/50 p-4 transition-colors hover:border-white/10"
          >
            {/* Un seul état pour « rien trouvé », pas trois : le port ne
                distingue pas un tracker injoignable ni un jeton expiré d'une
                recherche vide (les adaptateurs renvoient `[]` dans les trois
                cas). L'indice sur la connexion donne au moins une sortie à
                l'utilisateur dont le jeton a expiré. */}
            <div className="min-w-0">
              <span className="text-xs uppercase tracking-widest opacity-60">
                {TRACKER_LABELS[tracker]} : aucune correspondance
              </span>
              <p className="mt-1 text-[11px] leading-snug opacity-40">
                Si vous en attendiez une, vérifiez la connexion de ce compte dans votre profil.
              </p>
            </div>
            <Button size="sm" variant="outline" onClick={() => openSearch(tracker)}>
              <Search className="h-4 w-4" aria-hidden="true" />
              Chercher autre chose
            </Button>
          </div>
        ))}
      </div>

      <Modal
        isOpen={searchTracker !== null}
        onClose={closeSearch}
        title={searchTracker ? `Chercher sur ${TRACKER_LABELS[searchTracker]}` : ''}
        size="sm"
      >
        <div className="space-y-4">
          <div className="space-y-2">
            <label htmlFor={searchInputId} className="text-xs font-black uppercase opacity-60">
              Titre à rechercher
            </label>
            <div className="flex gap-2">
              <input
                id={searchInputId}
                type="text"
                aria-label="Titre à rechercher"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') void handleSearch();
                }}
                className="flex-1 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm"
              />
              <Button size="sm" onClick={() => void handleSearch()}>
                Rechercher
              </Button>
            </div>
          </div>

          <ul className="space-y-2">
            {results.map((candidate) => (
              <li key={candidate.remote_id}>
                <button
                  type="button"
                  onClick={() => void handlePick(candidate)}
                  className="flex w-full items-center justify-between rounded-xl border border-white/5 bg-white/5 px-4 py-3 text-left text-sm hover:border-white/10"
                >
                  <span className="font-bold italic">{candidate.title}</span>
                  {candidate.chapters != null && (
                    <span className="text-xs opacity-60">{candidate.chapters} ch.</span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </Modal>
    </section>
  );
};
