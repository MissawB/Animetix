import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from "../../store/authStore";
import { useTranslation } from 'react-i18next';
import { UserPlus, ArrowLeft, User, Mail, Lock } from 'lucide-react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const RegisterPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { register, isLoading } = useAuthStore();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!username || !email || !password) {
      setError(t('auth.fieldsRequired', 'Veuillez remplir tous les champs.'));
      return;
    }

    try {
      await register({ username, email, password });
      navigate('/');
    } catch (err) {
      const error = err as Error;
      setError(error.message || t('auth.registerFailed', "Erreur lors de l'inscription."));
    }
  };

  const inputClass =
    'w-full pl-12 pr-4 py-3.5 bg-gray-50 dark:bg-black/30 border-2 border-transparent focus:border-yellow-400 rounded-xl outline-none font-bold transition-all text-black dark:text-white placeholder:text-gray-400 dark:placeholder:text-gray-600';
  const iconClass = 'absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500 pointer-events-none';

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
              {t('auth.register.brand_desc', 'Rejoins la communauté otaku. Joue, grimpe au classement et crée tes propres défis — gratuitement.')}
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
              {t('auth.register.title_part1', 'REJOINS')} <span className="text-yellow-400">{t('auth.register.title_part2', "L'AVENTURE")}</span>
            </h1>
            <p className="mt-4 mb-10 text-base font-medium text-gray-500 dark:text-white/50">
              {t('auth.register.subtitle', "Crée ton compte en quelques secondes. C'est gratuit.")}
            </p>

            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-4 rounded-xl text-sm font-bold text-center">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="username" className="block text-xs font-black uppercase opacity-60 tracking-widest text-black dark:text-white">
                  {t('auth.register.username_label', 'Pseudo')}
                </label>
                <div className="relative">
                  <User className={iconClass} />
                  <input
                    id="username"
                    aria-label={t('auth.register.username_label', 'Pseudo')}
                    type="text"
                    autoComplete="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className={inputClass}
                    placeholder={t('auth.register.username_placeholder', 'ex. kenji_92')}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="email" className="block text-xs font-black uppercase opacity-60 tracking-widest text-black dark:text-white">
                  {t('auth.register.email_label', 'Email')}
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
                    autoComplete="new-password"
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
                  t('common.loading', 'Création...')
                ) : (
                  <>
                    <UserPlus className="w-5 h-5" /> {t('auth.register.submit', "S'INSCRIRE")}
                  </>
                )}
              </button>

              <div className="text-center pt-6 border-t border-gray-100 dark:border-white/5">
                <p className="text-sm opacity-60 font-bold text-black dark:text-white">
                  {t('auth.register.have_account', 'Déjà un compte ?')}{' '}
                  <Link to="/auth/login/" className="text-yellow-500 dark:text-yellow-400 hover:underline uppercase tracking-wide">
                    {t('auth.register.login_link', 'Se connecter')}
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

export default RegisterPage;
