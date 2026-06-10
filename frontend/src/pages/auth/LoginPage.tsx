import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { useTranslation } from 'react-i18next';
import { LogIn, ArrowLeft } from 'lucide-react';
import { AnimatedPage } from "../../components/ui/AnimatedPage";

const LoginPage: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loginWithGoogle, loginWithDiscord, loginWithX, isLoading } = useAuthStore();
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
    } catch (err: any) {
      setError(err.message || t('auth.loginFailed', 'Identifiants incorrects.'));
    }
  };

  const handleGoogleLogin = async () => {
    setError('');
    try {
      await loginWithGoogle();
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || t('auth.loginFailed', 'Connexion Google échouée.'));
    }
  };

  const handleDiscordLogin = async () => {
    setError('');
    try {
      await loginWithDiscord();
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || t('auth.loginFailed', 'Connexion Discord échouée.'));
    }
  };

  const handleXLogin = async () => {
    setError('');
    try {
      await loginWithX();
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || t('auth.loginFailed', 'Connexion X échouée.'));
    }
  };

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay p-6">
        <div className="max-w-md w-full animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Link to="/" className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-gray-500 hover:text-black dark:hover:text-white mb-8 no-underline transition-colors">
            <ArrowLeft className="w-4 h-4" /> Retour à l'accueil
          </Link>

          <h1 className="text-4xl md:text-5xl font-black italic manga-font mb-8 tracking-tighter uppercase text-center text-black dark:text-white">
            CONNEXION <span className="text-brand-primary">SYSTEME</span>
          </h1>

          <Card padding="lg" className="shadow-2xl border-none">
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-4 rounded-xl text-sm font-bold text-center">
                  {error}
                </div>
              )}
              
              <div className="space-y-2">
                <label htmlFor="email" className="text-xs font-black uppercase opacity-60 tracking-widest text-black dark:text-white">
                  Adresse Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-black/20 border-2 border-transparent focus:border-brand-primary rounded-xl px-4 py-3 outline-none font-bold transition-all text-black dark:text-white"
                  placeholder="Ex: user@domain.com"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="text-xs font-black uppercase opacity-60 tracking-widest text-black dark:text-white">
                  Mot de passe
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-black/20 border-2 border-transparent focus:border-brand-primary rounded-xl px-4 py-3 outline-none font-bold transition-all text-black dark:text-white"
                  placeholder="••••••••"
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                fullWidth
                disabled={isLoading}
                className="py-4 text-sm mt-4 font-black italic manga-font tracking-widest"
              >
                {isLoading ? t('common.loading', 'Chargement...') : <><LogIn className="w-5 h-5" /> SE CONNECTER</>}
              </Button>

              <div className="relative flex py-2 items-center">
                <div className="flex-grow border-t border-gray-200 dark:border-white/10"></div>
                <span className="flex-shrink mx-4 text-xs font-black uppercase opacity-60 tracking-widest text-black dark:text-white">OU</span>
                <div className="flex-grow border-t border-gray-200 dark:border-white/10"></div>
              </div>

              <Button
                type="button"
                variant="outline"
                fullWidth
                disabled={isLoading}
                onClick={handleGoogleLogin}
                className="py-4 text-sm font-black italic manga-font tracking-widest flex items-center justify-center gap-2 border-2 border-gray-200 dark:border-white/10"
              >
                <svg className="w-5 h-5 mr-1" viewBox="0 0 24 24">
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                SE CONNECTER AVEC GOOGLE
              </Button>

              <Button
                type="button"
                variant="outline"
                fullWidth
                disabled={isLoading}
                onClick={handleDiscordLogin}
                className="py-4 text-sm font-black italic manga-font tracking-widest flex items-center justify-center gap-2 border-2 border-gray-200 dark:border-white/10 mt-3"
              >
                <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028c.462-.63.874-1.295 1.226-1.994.021-.041.001-.09-.041-.106a13.094 13.094 0 0 1-1.873-.894.077.077 0 0 1-.008-.128c.126-.093.252-.19.372-.287a.075.075 0 0 1 .077-.011c3.92 1.793 8.18 1.793 12.061 0a.073.073 0 0 1 .078.009c.12.099.246.195.373.289a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.894.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.156 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.156-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.156 2.418z" />
                </svg>
                SE CONNECTER AVEC DISCORD
              </Button>

              <Button
                type="button"
                variant="outline"
                fullWidth
                disabled={isLoading}
                onClick={handleXLogin}
                className="py-4 text-sm font-black italic manga-font tracking-widest flex items-center justify-center gap-2 border-2 border-gray-200 dark:border-white/10 mt-3"
              >
                <svg className="w-5 h-5 mr-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
                SE CONNECTER AVEC X
              </Button>

              <div className="text-center pt-6 border-t border-gray-100 dark:border-white/5">
                <p className="text-sm opacity-60 font-bold text-black dark:text-white">
                  Pas encore de compte ?{' '}
                  <Link to="/auth/register/" className="text-brand-primary hover:underline uppercase tracking-wide">
                    Créer un compte
                  </Link>
                </p>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default LoginPage;
