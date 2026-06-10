import React, { useState } from 'react';
import { useAuthStore } from "../../store/authStore";
import { updateAccountSettings, generateApiKey, revokeApiKey } from '../../api';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { useTranslation } from 'react-i18next';
import { Settings, Key, ShieldAlert, Star, AlertTriangle, Eye, EyeOff, MessageSquare, ChevronRight } from 'lucide-react';
import { useToastStore } from "../../store/toastStore";
import { Link } from 'react-router-dom';

import { AnimatedPage } from "../../components/ui/AnimatedPage";

const AccountSettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const { user, checkAuth } = useAuthStore();
  const { addToast } = useToastStore();
  
  const [isUpdating, setIsUpdating] = useState(false);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const [showKey, setShowKey] = useState(false);

  if (!user) {
    return <div className="p-20 text-center">Vous devez être connecté.</div>;
  }

  const handleUpdateTier = async (newTier: string) => {
    setIsUpdating(true);
    try {
      await updateAccountSettings({ tier: newTier });
      await checkAuth(); // Refresh user data
      addToast(t('account.updateSuccess', 'Niveau mis à jour avec succès'), 'success');
    } catch (error) {
      addToast(t('account.updateError', 'Erreur lors de la mise à jour'), 'error');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleGenerateKey = async () => {
    if (!window.confirm("Générer une nouvelle clé révoquera l'ancienne. Continuer ?")) return;
    setIsUpdating(true);
    try {
      const response = await generateApiKey();
      setApiKey(response.api_key);
      await checkAuth();
      addToast(t('account.keyGenerated', 'Nouvelle clé API générée. Copiez-la maintenant !'), 'success');
    } catch (error) {
      addToast(t('account.keyError', 'Erreur lors de la génération de la clé'), 'error');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleRevokeKey = async () => {
    if (!window.confirm("Êtes-vous sûr de vouloir révoquer votre clé API ?")) return;
    setIsUpdating(true);
    try {
      await revokeApiKey();
      setApiKey(null);
      await checkAuth();
      addToast(t('account.keyRevoked', 'Clé API révoquée'), 'success');
    } catch (error) {
      addToast(t('account.revokeError', 'Erreur lors de la révocation'), 'error');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#fffcf0] dark:bg-[#1a1a2e] transition-colors duration-500 bg-manga-overlay">
        <div className="max-w-4xl mx-auto px-6 py-16 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <h1 className="text-4xl md:text-5xl font-black italic manga-font mb-12 tracking-tighter uppercase flex items-center gap-3 text-black dark:text-white">
            <Settings className="w-10 h-10 text-blue-500" /> GESTION DU <span className="text-blue-500">COMPTE</span>
          </h1>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            
            {/* Informations générales */}
            <Card padding="lg" className="space-y-6 shadow-xl border-none bg-white dark:bg-[#0f0f1a]">
              <h2 className="text-xl font-bold uppercase tracking-widest border-b border-gray-100 dark:border-white/5 pb-4 mb-4 text-black dark:text-white">
                Profil
              </h2>
              <div>
                <span className="text-[10px] font-black uppercase opacity-50 block mb-1 text-black dark:text-white">Nom d'utilisateur</span>
                <div className="font-bold text-lg bg-gray-50 dark:bg-black/20 px-4 py-2 rounded-xl border border-gray-100 dark:border-white/5 text-black dark:text-white">
                  {user.username}
                </div>
              </div>
              <div>
                <span className="text-[10px] font-black uppercase opacity-50 block mb-1 text-black dark:text-white">Email</span>
                <div className="font-bold text-lg bg-gray-50 dark:bg-black/20 px-4 py-2 rounded-xl border border-gray-100 dark:border-white/5 text-black dark:text-white">
                  {user.email || 'Non renseigné'}
                </div>
              </div>
            </Card>

            {/* Statut & Sponsors */}
            <Card padding="lg" className="space-y-6 shadow-xl border-none bg-white dark:bg-[#0f0f1a]">
              <h2 className="text-xl font-bold uppercase tracking-widest border-b border-gray-100 dark:border-white/5 pb-4 mb-4 flex items-center gap-2 text-black dark:text-white">
                <Star className="w-5 h-5 text-yellow-400" /> Statut du Compte
              </h2>
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-gray-50 dark:bg-black/20 border border-gray-100 dark:border-white/5 space-y-2 text-black dark:text-white">
                  <span className="text-[10px] font-black uppercase opacity-50 block">Votre Statut Actuel</span>
                  <span className="font-bold text-lg uppercase text-yellow-500">
                    {user.tier === 'premium' ? 'Boosté (Sponsorisé)' : 'Standard (Financé par Pubs)'}
                  </span>
                </div>
                <p className="text-xs text-gray-500">
                  {user.tier === 'premium' 
                    ? "Votre boost est actif. Vous profitez d'une expérience sans publicité." 
                    : "Votre compte est actuellement en mode standard. Pour supprimer les publicités et multiplier votre quota IA par 5, visitez l'Espace Sponsors."}
                </p>
                <Link to="/pricing/" className="block text-center bg-yellow-500 hover:bg-yellow-600 text-black font-black italic manga-font text-xs py-4 px-6 rounded-xl shadow-lg transition-all no-underline">
                  ACCÉDER À L'ESPACE SPONSORS
                </Link>
              </div>
            </Card>

            {/* Historique IA */}
            <Card padding="lg" className="md:col-span-2 space-y-6 shadow-xl border-none bg-white dark:bg-[#0f0f1a]">
              <h2 className="text-xl font-bold uppercase tracking-widest border-b border-gray-100 dark:border-white/5 pb-4 mb-4 flex items-center gap-2 text-black dark:text-white">
                <MessageSquare className="w-5 h-5 text-purple-500" /> Vos Contributions IA
              </h2>
              <p className="text-sm opacity-60 text-black dark:text-white">
                Retrouvez l'historique de vos feedbacks et aidez l'intelligence d'Animetix à s'améliorer.
              </p>
              <Link 
                to="/social/ai-feedback-history/" 
                className="flex items-center justify-between bg-gray-50 dark:bg-black/20 p-4 rounded-xl border border-gray-100 dark:border-white/5 hover:border-brand-primary transition-all no-underline text-black dark:text-white group"
              >
                <span className="font-bold uppercase tracking-widest text-xs">Accéder à l'historique complet</span>
                <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-brand-primary group-hover:translate-x-1 transition-all" />
              </Link>
            </Card>

            {/* Clé API */}
            <Card padding="lg" className="md:col-span-2 space-y-6 border-2 border-red-500/20 bg-white dark:bg-[#0f0f1a] shadow-xl">
              <h2 className="text-xl font-bold uppercase tracking-widest border-b border-gray-100 dark:border-white/5 pb-4 mb-4 flex items-center gap-2 text-red-500">
                <Key className="w-5 h-5" /> Accès Développeur (API)
              </h2>
              
              <div className="bg-red-500/5 p-4 rounded-xl border border-red-500/20 flex gap-3 text-red-400">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <p className="text-sm font-bold">
                  Votre clé API vous permet d'accéder au backend Headless en externe. Ne la partagez jamais. Si elle est compromise, révoquez-la immédiatement.
                </p>
              </div>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-black dark:text-white">Statut de la clé :</span>
                  <span className={`px-3 py-1 rounded-full text-xs font-black uppercase tracking-widest ${user.has_api_key ? 'bg-green-500/20 text-green-500' : 'bg-gray-500/20 text-gray-500'}`}>
                    {user.has_api_key ? 'Active' : 'Aucune'}
                  </span>
                </div>

                {apiKey && (
                  <div className="mt-4 space-y-2">
                    <span className="text-xs font-black uppercase text-brand-primary">Votre nouvelle clé (Copiez-la maintenant !)</span>
                    <div className="flex gap-2">
                      <div className="flex-1 bg-gray-900 text-green-400 font-mono p-3 rounded-lg border border-gray-700 overflow-x-auto">
                        {showKey ? apiKey : '•'.repeat(apiKey.length)}
                      </div>
                      <Button variant="outline" onClick={() => setShowKey(!showKey)}>
                        {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </Button>
                    </div>
                  </div>
                )}

                <div className="flex gap-4 pt-4">
                  <Button 
                    variant="primary" 
                    onClick={handleGenerateKey} 
                    disabled={isUpdating}
                    className="font-black italic manga-font text-xs"
                  >
                    <Key className="w-4 h-4 mr-2" /> Générer une nouvelle clé
                  </Button>
                  {user.has_api_key && (
                    <Button 
                      variant="outline" 
                      onClick={handleRevokeKey} 
                      disabled={isUpdating}
                      className="text-red-500 hover:bg-red-500 hover:text-white border-red-500/20 font-black italic manga-font text-xs"
                    >
                      <ShieldAlert className="w-4 h-4 mr-2" /> Révoquer
                    </Button>
                  )}
                </div>
              </div>
            </Card>

          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AccountSettingsPage;

