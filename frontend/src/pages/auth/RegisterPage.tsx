import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from "../../store/authStore";
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { useTranslation } from 'react-i18next';
import { UserPlus, ArrowLeft } from 'lucide-react';
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

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] flex items-center justify-center bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay p-6">
        <div className="max-w-md w-full animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Link to="/" className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-widest text-gray-500 hover:text-black dark:hover:text-white mb-8 no-underline transition-colors">
            <ArrowLeft className="w-4 h-4" /> Retour à l'accueil
          </Link>
          
          <h1 className="text-4xl md:text-5xl font-black italic manga-font mb-8 tracking-tighter uppercase text-center text-black dark:text-white">
            REJOINDRE <span className="text-brand-primary">L'AVENTURE</span>
          </h1>
          
          <Card padding="lg" className="shadow-2xl border-none">
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-4 rounded-xl text-sm font-bold text-center">
                  {error}
                </div>
              )}
              
              <div className="space-y-2">
                <label htmlFor="username" className="text-xs font-black uppercase opacity-60 tracking-widest text-black dark:text-white">
                  Nom d'utilisateur
                </label>
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-black/20 border-2 border-transparent focus:border-brand-primary rounded-xl px-4 py-3 outline-none font-bold transition-all text-black dark:text-white"
                  placeholder="Héros ou Héroïne"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="email" className="text-xs font-black uppercase opacity-60 tracking-widest text-black dark:text-white">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-black/20 border-2 border-transparent focus:border-brand-primary rounded-xl px-4 py-3 outline-none font-bold transition-all text-black dark:text-white"
                  placeholder="contact@animetix.com"
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
                {isLoading ? t('common.loading', 'Création...') : <><UserPlus className="w-5 h-5" /> S'INSCRIRE</>}
              </Button>

              <div className="text-center pt-6 border-t border-gray-100 dark:border-white/5">
                <p className="text-sm opacity-60 font-bold text-black dark:text-white">
                  Déjà un compte ?{' '}
                  <Link to="/auth/login/" className="text-brand-primary hover:underline uppercase tracking-wide">
                    Se connecter
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

export default RegisterPage;


