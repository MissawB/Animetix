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
