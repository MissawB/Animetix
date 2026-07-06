import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from "../../store/authStore";
import { useTranslation } from 'react-i18next';
import { LogIn, ArrowLeft, Mail, Lock } from 'lucide-react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const LoginPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loginWithGoogle, isLoading } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const from = location.state?.from?.pathname || '/';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!email || !password) {
      setError(t('auth.fieldsRequired', 'Veuillez remplir tous les champs.'));
      return;
    }

    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch (err) {
      const error = err as Error;
      setError(error.message || t('auth.loginFailed', 'Identifiants incorrects.'));
    }
  };

  const handleGoogleLogin = async () => {
    setError('');
    try {
      await loginWithGoogle();
      navigate(from, { replace: true });
    } catch (err) {
      const error = err as Error;
      setError(error.message || t('auth.loginFailed', 'Connexion Google échouée.'));
    }
  };

  const inputClass =
    'w-full pl-12 pr-4 py-3.5 bg-gray-50 dark:bg-black/30 border-2 border-transparent focus:border-yellow-400 rounded-xl outline-none font-bold transition-all text-black dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600';
  const iconClass = 'absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500 pointer-events-none';
  const socialBtn =
    'flex items-center justify-center py-3.5 rounded-xl border-2 border-gray-200 dark:border-white/10 hover:border-yellow-400 hover:bg-yellow-400/5 transition-all disabled:opacity-50 disabled:cursor-not-allowed';
  // Discord/X/MAL OIDC providers aren't configured yet — keep them disabled.
  const socialBtnSoon =
    'flex items-center justify-center py-3.5 rounded-xl border-2 border-gray-200 dark:border-white/10 opacity-40 grayscale cursor-not-allowed';

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] flex bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500">
        {/* ── Brand panel ───────────────────────────────────────── */}
        <aside className="hidden lg:flex lg:w-[45%] xl:w-1/2 relative overflow-hidden bg-gradient-to-br from-[#0f0f1a] via-[#14142a] to-[#1a1a2e] flex-col items-center justify-center text-center p-12 xl:p-16">
          <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-20 mix-blend-overlay" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[460px] h-[460px] rounded-full bg-yellow-400/10 blur-[130px]" />

          <div className="relative z-10 flex flex-col items-center w-full max-w-sm">
            <img
              src="/static/img/logo/white_logo.png"
              alt="Animetix"
              className="w-40 xl:w-48 invert drop-shadow-[0_0_70px_rgba(253,185,19,0.35)] select-none"
              loading="lazy"
              decoding="async"
            />
            <span className="manga-font text-white text-4xl tracking-tighter mt-6">
              ANIME<span className="text-yellow-400">TIX</span>
            </span>
            <p className="mt-2 text-sm font-bold uppercase tracking-[0.25em] text-white/40 italic">
              {t('auth.brand_tagline', "L'IA au service de ta passion")}
            </p>
            <p className="mt-8 text-white/50 text-base font-medium leading-snug">
              {t('auth.login.brand_desc', "Ton aventure reprend là où tu l'as laissée. Classements, défis et créations t'attendent.")}
            </p>
          </div>
        </aside>

        {/* ── Form panel ────────────────────────────────────────── */}
        <main className="flex-1 flex items-center justify-center p-6 sm:p-10">
          <div className="w-full max-w-md animate-in fade-in slide-in-from-bottom-4 duration-500">
            <Link
              to="/"
              className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-gray-500 hover:text-black dark:hover:text-white mb-10 no-underline transition-colors"
            >
              <ArrowLeft className="w-4 h-4" /> {t('auth.back_home', "Retour à l'accueil")}
            </Link>

            <h1 className="text-4xl md:text-5xl font-black italic manga-font tracking-tighter uppercase text-black dark:text-white leading-none">
              {t('auth.login.title_part1', 'CONTENT DE TE')} <span className="text-yellow-400">{t('auth.login.title_part2', 'REVOIR')}</span>
            </h1>
            <p className="mt-4 mb-10 text-base font-medium text-gray-500 dark:text-white/50">
              {t('auth.login.subtitle', 'Connecte-toi pour reprendre la partie.')}
            </p>

            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-4 rounded-xl text-sm font-bold text-center">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="email" className="block text-xs font-black uppercase opacity-60 tracking-widest text-black dark:text-white">
                  {t('auth.email_address', 'Adresse email')}
                </label>
                <div className="relative">
                  <Mail className={iconClass} />
                  <input
                    id="email"
                    aria-label={t('auth.email_address', 'Adresse email')}
                    type="email"
                    autoComplete="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={inputClass}
                    placeholder="contact@animetix.com"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-xs font-black uppercase opacity-60 tracking-widest text-black dark:text-white">
                  {t('auth.password', 'Mot de passe')}
                </label>
                <div className="relative">
                  <Lock className={iconClass} />
                  <input
                    id="password"
                    aria-label={t('auth.password', 'Mot de passe')}
                    type="password"
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={inputClass}
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 bg-yellow-400 hover:bg-yellow-500 text-black font-black italic manga-font tracking-widest py-4 rounded-xl border-2 border-black/10 shadow-xl hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-60 disabled:hover:scale-100 mt-2"
              >
                {isLoading ? (
                  t('common.loading', 'Chargement...')
                ) : (
                  <>
                    <LogIn className="w-5 h-5" /> {t('auth.login.submit', 'SE CONNECTER')}
                  </>
                )}
              </button>

              <div className="relative flex py-1 items-center">
                <div className="flex-grow border-t border-gray-200 dark:border-white/10"></div>
                <span className="flex-shrink mx-4 text-xs font-black uppercase opacity-50 tracking-widest text-black dark:text-white">
                  {t('auth.login.social_title', 'Connexions sociales')}
                </span>
                <div className="flex-grow border-t border-gray-200 dark:border-white/10"></div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <button type="button" aria-label={t('auth.login.google_aria', 'Se connecter avec Google')} title="Google" disabled={isLoading} onClick={handleGoogleLogin} className={socialBtn}>
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                  </svg>
                </button>

                <button type="button" aria-label={t('auth.login.discord_soon_aria', 'Discord — bientôt disponible')} title={t('auth.login.soon', 'Bientôt disponible')} disabled className={socialBtnSoon}>
                  <svg className="w-5 h-5 text-[#5865F2]" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.094 13.094 0 0 1-1.873-.894.077.077 0 0 1-.008-.128c.126-.093.252-.19.372-.287a.075.075 0 0 1 .077-.011c3.92 1.793 8.18 1.793 12.061 0a.073.073 0 0 1 .078.009c.12.099.246.195.373.289a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.156 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.156 2.418z" />
                  </svg>
                </button>

                <button type="button" aria-label={t('auth.login.mal_soon_aria', 'MyAnimeList — bientôt disponible')} title={t('auth.login.soon', 'Bientôt disponible')} disabled className={socialBtnSoon}>
                  <svg className="w-5 h-5 text-[#2e51a2]" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                    <path d="M14.921 6.479c-.82 0-3.683 0-4.947 3.156-.662 1.652-.986 4.812.876 7.886l1.934-1.41s-.767-1.095-1.083-3.191h2.897l.022 3.19h2.604V8.835h-2.581v2.043l-2.46-.023s.413-2.408 2.877-2.336h2.454l-.572-2.04ZM0 6.528v9.624h2.348v-5.84l2.031 2.664 2.047-2.652v5.828h2.336V6.528H6.437L4.368 9.474 2.31 6.528Zm18.447.022v9.583h5.022L24 14.09h-3.232V6.55Z" />
                  </svg>
                </button>
              </div>
              <p className="text-center text-[10px] font-black uppercase tracking-widest text-gray-400 dark:text-gray-500 mt-3">
                {t('auth.login.social_soon_note', 'Discord & MyAnimeList bientôt disponibles')}
              </p>

              <div className="text-center pt-6 border-t border-gray-100 dark:border-white/5">
                <p className="text-sm opacity-60 font-bold text-black dark:text-white">
                  {t('auth.login.no_account', 'Pas encore de compte ?')}{' '}
                  <Link to="/auth/register/" className="text-yellow-500 dark:text-yellow-400 hover:underline uppercase tracking-wide">
                    {t('auth.login.create_account', 'Créer un compte')}
                  </Link>
                </p>
              </div>
            </form>
          </div>
        </main>
      </div>
    </AnimatedPage>
  );
};

export default LoginPage;
