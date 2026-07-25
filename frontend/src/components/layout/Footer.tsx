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

interface FooterLink {
  to: string;
  label: string;
}
interface FooterColumn {
  title: string;
  glyph: string;
  links: FooterLink[];
}

const Footer: React.FC = () => {
  const { t } = useTranslation();
  const year = new Date().getFullYear();

  const columns: FooterColumn[] = [
    {
      title: t('footer.col_play', 'Jouer'),
      glyph: '遊',
      links: [
        { to: '/games/hub/', label: t('nav.games', 'Jeux') },
        { to: '/daily-challenge/', label: t('nav.daily', 'Défi Quotidien') },
        { to: '/leaderboard/', label: t('nav.leaderboard', 'Classement') },
      ],
    },
    {
      title: t('footer.col_explore', 'Explorer'),
      glyph: '探',
      links: [
        { to: '/search/', label: t('nav.search', 'Recherche') },
        { to: '/explore/', label: t('nav.explore', 'Explorer') },
        { to: '/media/manga/library/', label: t('nav.library', 'Ma Bibliothèque') },
      ],
    },
    {
      title: t('footer.col_create', 'Créer'),
      glyph: '創',
      links: [
        { to: '/lab/forge-hub/', label: t('nav.forge', 'Forge Créative') },
        { to: '/lab/', label: t('nav.labs_hub', 'Labs') },
        { to: '/research/papers/', label: t('nav.research', 'Recherche IA') },
      ],
    },
    {
      title: t('footer.col_community', 'Communauté'),
      glyph: '会',
      links: [
        { to: '/social/dashboard/', label: t('nav.community', 'Communauté') },
        { to: '/social/nexus/', label: t('nav.nexus', 'Nexus Pro') },
        { to: '/social/transparency/', label: t('navbar.transparency', 'Transparence') },
        { to: '/social/open-data/', label: t('nav.open_data', 'Portail Open Data') },
      ],
    },
  ];

  return (
    <footer className="relative mt-auto overflow-hidden border-t border-[#F4F1E8]/10 bg-[#0B0C10] text-[#F4F1E8]">
      {/* Filet éditorial shu — la signature de l'édition de nuit */}
      <div className="h-px w-full bg-gradient-to-r from-[#E8442B] via-[#E8442B]/30 to-transparent" />
      {/* Trame halftone en tête de colophon */}
      <div
        className="explore-halftone pointer-events-none absolute inset-x-0 top-0 h-40"
        aria-hidden
      />
      {/* Sceau « okuzuke » (colophon), en filigrane */}
      <span
        className="font-manga pointer-events-none absolute -bottom-16 right-2 select-none text-[13rem] font-black italic leading-none text-[#F4F1E8]/[0.03]"
        aria-hidden
      >
        奥付
      </span>

      <div className="relative max-w-7xl mx-auto px-6 lg:px-10 pt-14 pb-8">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-x-8 gap-y-10">
          {/* Bloc marque */}
          <div className="col-span-2 lg:col-span-2 pr-4">
            <Link to="/" className="inline-flex items-center gap-2.5 no-underline group">
              <img
                src="/static/img/logo/white_logo.png"
                alt="Animetix"
                className="w-9 h-9 object-contain transition-transform group-hover:rotate-6"
              />
              <span className="font-manga text-2xl font-black italic uppercase tracking-tighter text-[#F4F1E8]">
                ANIME<span className="text-[#E8442B]">TIX</span>
              </span>
            </Link>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-[#8F94A5]">
              {t(
                'footer.tagline',
                "Le terrain de jeu ultime pour fans d'anime & manga — quiz, déduction et création propulsés par l'IA.",
              )}
            </p>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={t('footer.github_aria', 'Code source sur GitHub')}
              className="mt-5 inline-flex items-center gap-2 rounded-full border border-[#F4F1E8]/15 px-4 py-2 text-xs font-black uppercase tracking-widest text-[#8F94A5] no-underline transition-colors hover:border-[#FDB913] hover:text-[#F4F1E8]"
            >
              <GithubIcon className="w-4 h-4" /> {t('footer.github', 'Code source')}
            </a>
          </div>

          {/* Colonnes de liens */}
          {columns.map((col) => (
            <nav key={col.title} aria-label={col.title} className="min-w-0">
              <h3 className="mb-4 flex items-center gap-2 text-[11px] font-black uppercase tracking-[0.18em] text-[#8F94A5]">
                <span
                  className="text-base font-black not-italic leading-none text-[#E8442B]"
                  aria-hidden
                >
                  {col.glyph}
                </span>
                {col.title}
              </h3>
              <ul className="space-y-2.5">
                {col.links.map((link) => (
                  <li key={link.to}>
                    <Link
                      to={link.to}
                      className="group inline-flex items-center gap-2 text-sm font-medium text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8]"
                    >
                      <span className="h-1 w-1 rounded-[1px] bg-[#E8442B] opacity-0 transition-opacity group-hover:opacity-100" />
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          ))}
        </div>

        {/* Barre de pied */}
        <div className="mt-14 flex flex-col items-center justify-between gap-4 border-t border-[#F4F1E8]/10 pt-6 sm:flex-row">
          <p className="order-3 text-xs font-medium text-[#8F94A5] sm:order-1">
            &copy; {year} Animetix Team. {t('footer.rights', 'Tous droits réservés.')}
          </p>
          <nav className="order-2 flex flex-wrap items-center justify-center gap-x-5 gap-y-2">
            <Link
              to="/about/"
              className="text-xs font-medium text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8]"
            >
              {t('nav.about', 'À propos')}
            </Link>
            <Link
              to="/privacy/"
              className="text-xs font-medium text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8]"
            >
              {t('nav.privacy', 'Politique de confidentialité')}
            </Link>
            <Link
              to="/contact/"
              className="text-xs font-medium text-[#8F94A5] no-underline transition-colors hover:text-[#F4F1E8]"
            >
              {t('nav.contact', 'Contact')}
            </Link>
          </nav>
          <div className="order-1 flex items-center gap-2 sm:order-3">
            <span className="relative flex h-2 w-2" aria-hidden>
              <span className="absolute inline-flex h-full w-full rounded-full bg-[#FDB913] opacity-60 animate-ping" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[#FDB913]" />
            </span>
            <p className="font-manga text-[10px] font-black uppercase tracking-[0.28em] text-[#8F94A5]">
              {t('footer.powered_by', 'Powered by Animetix IA & React 19')}
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default React.memo(Footer);
