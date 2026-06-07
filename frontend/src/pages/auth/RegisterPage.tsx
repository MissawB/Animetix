import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../../../store/authStore';
import { Card } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { useTranslation } from 'react-i18next';
import { UserPlus } from 'lucide-react';

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
    } catch (err: any) {
      setError(err.message || t('auth.registerFailed', "Erreur lors de l'inscription."));
    }
  };

  return (
    <div className="max-w-md mx-auto px-6 py-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <h1 className="text-4xl font-black italic manga-font mb-8 tracking-tighter uppercase text-center">
        REJOINDRE L'AVENTURE
      </h1>
      <Card padding="lg">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-500/10 border border-red-500/50 text-red-500 p-4 rounded-xl text-sm font-bold text-center">
              {error}
            </div>
          )}
          
          <div className="space-y-2">
            <label className="text-xs font-black uppercase opacity-60 tracking-widest">
              Nom d'utilisateur
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-brand-primary rounded-xl px-4 py-3 outline-none font-bold transition-all"
              placeholder="Héros ou Héroïne"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-black uppercase opacity-60 tracking-widest">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-brand-primary rounded-xl px-4 py-3 outline-none font-bold transition-all"
              placeholder="contact@animetix.com"
            />
          </div>

          <div className="space-y-2">
            <label className="text-xs font-black uppercase opacity-60 tracking-widest">
              Mot de passe
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-gray-50 dark:bg-navy-900 border-2 border-transparent focus:border-brand-primary rounded-xl px-4 py-3 outline-none font-bold transition-all"
              placeholder="••••••••"
            />
          </div>

          <Button
            type="submit"
            variant="primary"
            fullWidth
            disabled={isLoading}
            className="py-4 text-sm mt-4"
          >
            {isLoading ? t('common.loading', 'Création...') : <><UserPlus className="w-5 h-5" /> S'INSCRIRE</>}
          </Button>

          <div className="text-center pt-6 border-t border-gray-100 dark:border-white/5">
            <p className="text-sm opacity-60 font-bold">
              Déjà un compte ?{' '}
              <Link to="/login" className="text-brand-primary hover:underline uppercase tracking-wide">
                Se connecter
              </Link>
            </p>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default RegisterPage;

