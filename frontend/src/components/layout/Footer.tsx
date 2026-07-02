import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

const GITHUB_URL = 'https://github.com/MissawB/Animetix';

// lucide-react dropped brand icons, so the GitHub mark is inlined.
const GithubIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M12 .5C5.37.5 0 5.87 0 12.5c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58 0-.29-.01-1.04-.02-2.04-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.73.08-.73 1.2.08 1.84 1.24 1.84 1.24 1.07 1.83 2.81 1.3 3.5.99.11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.12-.3-.54-1.52.12-3.18 0 0 1.01-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.29-1.55 3.3-1.23 3.3-1.23.66 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.81 5.62-5.49 5.92.43.37.81 1.1.81 2.22 0 1.6-.01 2.89-.01 3.28 0 .32.21.7.82.58C20.56 22.29 24 17.8 24 12.5 24 5.87 18.63.5 12 .5z" />
  </svg>
);

interface FooterLink { to: string; label: string }
interface FooterColumn { title: string; links: FooterLink[] }

const Footer: React.FC = () => {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  const columns: FooterColumn[] = [
    {
      title: t('footer.col_play', 'Jouer'),
      links: [
        { to: '/games/hub/', label: t('nav.games', 'Jeux') },
        { to: '/daily-challenge/', label: t('nav.daily', 'Défi Quotidien') },
        { to: '/leaderboard/', label: t('nav.leaderboard', 'Classement') },
      ],
    },
    {
      title: t('footer.col_explore', 'Explorer'),
      links: [
        { to: '/search/', label: t('nav.search', 'Recherche') },
        { to: '/explore/', label: t('nav.explore', 'Explorer') },
        { to: '/media/manga/library/', label: t('nav.library', 'Ma Bibliothèque') },
      ],
    },
    {
      title: t('footer.col_create', 'Créer'),
      links: [
        { to: '/lab/forge-hub/', label: t('nav.forge', 'Forge Créative') },
        { to: '/lab/', label: t('nav.labs_hub', 'Labs') },
        { to: '/research/papers/', label: t('nav.research', 'Recherche IA') },
      ],
    },
    {
      title: t('footer.col_community', 'Communauté'),
      links: [
        { to: '/social/dashboard/', label: t('nav.community', 'Communauté') },
        { to: '/social/nexus/', label: t('nav.nexus', 'Nexus Pro') },
        { to: '/social/transparency/', label: t('navbar.transparency', 'Transparence') },
        { to: '/social/open-data/', label: t('nav.open_data', 'Portail Open Data') },
      ],
    },
  ];

  return (
    <footer className="relative mt-auto bg-[#fffcf0] dark:bg-[#13132a] border-t border-black/5 dark:border-white/5 transition-colors duration-500">
      {/* Accent hairline — the brand's blue→yellow signature */}
      <div className="h-px w-full bg-gradient-to-r from-transparent via-blue-500/60 to-yellow-400/70" />

      <div className="max-w-7xl mx-auto px-6 lg:px-10 pt-14 pb-8">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-x-8 gap-y-10">
          {/* Brand block */}
          <div className="col-span-2 lg:col-span-2 pr-4">
            <Link to="/" className="inline-flex items-center gap-2.5 no-underline group">
              <img
                src="/static/img/logo/white_logo.png"
                alt="Animetix"
                className="w-9 h-9 object-contain dark:invert transition-transform group-hover:rotate-6"
              />
              <span className="manga-font text-2xl tracking-tighter text-black dark:text-white">
                ANIME<span className="text-yellow-700 dark:text-yellow-400">TIX</span>
              </span>
            </Link>
            <p className="mt-4 text-sm font-medium leading-relaxed text-gray-500 dark:text-gray-400 max-w-xs">
              {t('footer.tagline', "Le terrain de jeu ultime pour fans d'anime & manga — quiz, déduction et création propulsés par l'IA.")}
            </p>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="Code source sur GitHub"
              className="mt-5 inline-flex items-center gap-2 rounded-xl border border-black/10 dark:border-white/10 px-3.5 py-2 text-xs font-black uppercase tracking-wide text-gray-600 dark:text-gray-300 no-underline hover:border-yellow-400 hover:text-black dark:hover:text-white transition-colors"
            >
              <GithubIcon className="w-4 h-4" /> {t('footer.github', 'Code source')}
            </a>
          </div>

          {/* Link columns */}
          {columns.map((col) => (
            <nav key={col.title} aria-label={col.title} className="min-w-0">
              <h3 className="text-[11px] font-black uppercase tracking-[0.18em] text-gray-600 dark:text-gray-400 mb-4">
                {col.title}
              </h3>
              <ul className="space-y-2.5">
                {col.links.map((link) => (
                  <li key={link.to}>
                    <Link
                      to={link.to}
                      className="group inline-flex items-center gap-1.5 text-sm font-bold text-gray-600 dark:text-gray-300 no-underline hover:text-black dark:hover:text-white transition-colors"
                    >
                      <span className="h-1 w-1 rounded-full bg-yellow-400/0 group-hover:bg-yellow-400 transition-colors" />
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        {/* Bottom bar */}
        <div className="mt-14 pt-6 border-t border-black/5 dark:border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs font-bold text-gray-500 dark:text-gray-400 order-2 sm:order-1">
            &copy; {year} Animetix Team. {t('footer.rights', 'Tous droits réservés.')}
          </p>
          <div className="flex items-center gap-2 order-1 sm:order-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-60 animate-ping" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-500" />
            </span>
            <p className="manga-font text-[10px] tracking-[0.28em] text-gray-500 dark:text-gray-400">
              {t('footer.powered_by', 'Powered by Animetix IA & React 19')}
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default React.memo(Footer);
