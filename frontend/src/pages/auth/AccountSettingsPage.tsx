import React, { useState } from 'react';
import { useAuthStore } from "../../store/authStore";
import { updateAccountSettings } from '../../api';
import { Card } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import {Settings, Star, ChevronRight, Sparkles, BarChart3, Terminal} from 'lucide-react';
import { useToastStore } from "../../store/toastStore";
import { Link } from 'react-router-dom';

import { AnimatedPage } from "../../components/ui/AnimatedPage";

const PRESET_COLORS = [
  { name: 'Sponsor Or', hex: '#FFD700' },
  { name: 'Néon Cyber', hex: '#00FFCC' },
  { name: 'Rose Sakura', hex: '#FF66B2' },
  { name: 'Rouge Fureur', hex: '#FF3333' },
  { name: 'Bleu Abysse', hex: '#3366FF' }
];

const AccountSettingsPage: React.FC = () => {
  const { user, refetchUser } = useAuthStore();
  const { addToast } = useToastStore();

  const [customColor, setCustomColor] = useState(user?.custom_username_color || '#FFD700');
  const [isSavingColor, setIsSavingColor] = useState(false);

  if (!user) {
    return <div className="p-20 text-center">Vous devez être connecté.</div>;
  }
  const handleSaveColor = async (colorToSave: string) => {
    setIsSavingColor(true);
    try {
      await updateAccountSettings({ custom_username_color: colorToSave });
      await refetchUser();
      addToast("Couleur du pseudo mise à jour !", "success");
    } catch (error) {
      console.error(error);
      addToast("Erreur lors de la mise à jour de la couleur.", "error");
    } finally {
      setIsSavingColor(false);
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
                <Link to="/power-station/" className="block text-center bg-yellow-500 hover:bg-yellow-600 text-black font-black italic manga-font text-xs py-4 px-6 rounded-xl shadow-lg transition-all no-underline">
                  ACCÉDER À L'ESPACE SPONSORS
                </Link>
              </div>
            </Card>

            {/* Personnalisation Cosmétique */}
            <Card padding="lg" className="space-y-6 shadow-xl border-none bg-white dark:bg-[#0f0f1a] relative overflow-hidden flex flex-col justify-between">
              <div>
                <h2 className="text-xl font-bold uppercase tracking-widest border-b border-gray-100 dark:border-white/5 pb-4 mb-4 flex items-center gap-2 text-black dark:text-white">
                  <Sparkles className="w-5 h-5 text-yellow-500" /> Couleur du Pseudo
                </h2>
                
                {user.unlocked_badges?.includes('Sponsor Or') ? (
                  <div className="space-y-6">
                    <p className="text-xs text-gray-500">
                      Personnalisez l'affichage de votre pseudo sur votre profil public.
                    </p>
                    
                    {/* Preview */}
                    <div className="p-4 rounded-2xl bg-gray-50 dark:bg-black/20 border border-gray-100 dark:border-white/5 text-center">
                      <span className="text-[10px] font-black uppercase opacity-40 block mb-2 text-black dark:text-white">Aperçu du Profil</span>
                      <span 
                        className="text-2xl font-black italic manga-font uppercase tracking-tighter"
                        style={{ color: customColor || undefined }}
                      >
                        {user.username}
                      </span>
                    </div>

                    {/* Presets */}
                    <div className="space-y-2">
                      <span className="text-[10px] font-black uppercase opacity-50 block text-black dark:text-white">Couleurs Prédéfinies</span>
                      <div className="flex flex-wrap gap-3">
                        {PRESET_COLORS.map((preset) => (
                          <button
                            key={preset.hex}
                            onClick={() => setCustomColor(preset.hex)}
                            title={preset.name}
                            aria-label={`Couleur ${preset.name}`}
                            className={`w-8 h-8 rounded-full border-2 transition-all ${
                              customColor === preset.hex ? 'border-black dark:border-white scale-110 shadow-lg' : 'border-transparent hover:scale-105'
                            }`}
                            style={{ backgroundColor: preset.hex }}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Custom Color Picker */}
                    <div className="flex items-center gap-4">
                      <div className="space-y-1">
                        <span className="text-[10px] font-black uppercase opacity-50 block text-black dark:text-white">Couleur Personnalisée</span>
                        <input
                          type="color"
                          aria-label="Couleur personnalisée"
                          value={customColor || '#FFD700'}
                          onChange={(e) => setCustomColor(e.target.value)}
                          className="w-12 h-10 rounded-xl border border-gray-200 dark:border-white/10 cursor-pointer bg-transparent"
                        />
                      </div>
                      <div className="flex-1 space-y-1">
                        <span className="text-[10px] font-black uppercase opacity-50 block text-black dark:text-white">Code Hex</span>
                        <input
                          type="text"
                          aria-label="Code hexadécimal de la couleur"
                          value={customColor}
                          onChange={(e) => {
                            const val = e.target.value;
                            if (val === "" || val.startsWith("#")) {
                              setCustomColor(val);
                            }
                          }}
                          placeholder="#FFD700"
                          className="w-full bg-gray-50 dark:bg-black/20 px-3 py-2 rounded-xl border border-gray-100 dark:border-white/5 text-sm font-mono text-black dark:text-white"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="relative py-12 text-center space-y-4">
                    <div className="mx-auto w-12 h-12 bg-gray-100 dark:bg-white/5 rounded-2xl flex items-center justify-center text-gray-400 dark:text-gray-600">
                      🔒
                    </div>
                    <div className="space-y-1">
                      <p className="font-bold text-sm text-black dark:text-white">Fonctionnalité Verrouillée</p>
                      <p className="text-xs text-gray-500 max-w-xs mx-auto">
                        Soutenez Animetix dans l'Espace Sponsors pour débloquer le badge exclusif et la couleur de pseudo personnalisée !
                      </p>
                    </div>
                    <Link to="/power-station/" className="inline-block text-xs font-black uppercase tracking-wider text-yellow-500 hover:text-yellow-600 no-underline">
                      Devenir Sponsor →
                    </Link>
                  </div>
                )}
              </div>

              {user.unlocked_badges?.includes('Sponsor Or') && (
                <div className="flex gap-3 pt-4 border-t border-gray-100 dark:border-white/5">
                  <Button
                    variant="primary"
                    size="sm"
                    className="flex-1 font-black italic manga-font text-xs"
                    onClick={() => handleSaveColor(customColor)}
                    disabled={isSavingColor}
                  >
                    {isSavingColor ? "Enregistrement..." : "Enregistrer"}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    className="font-black italic manga-font text-xs text-red-500 hover:bg-red-500 hover:text-white border-red-500/10"
                    onClick={() => {
                      setCustomColor("");
                      handleSaveColor("").then();
                    }}
                    disabled={isSavingColor}
                  >
                    Réinitialiser
                  </Button>
                </div>
              )}
            </Card>

            {/* Historique IA */}
            <Card padding="lg" className="space-y-6 shadow-xl border-none bg-white dark:bg-[#0f0f1a]">
              <h2 className="text-xl font-bold uppercase tracking-widest border-b border-gray-100 dark:border-white/5 pb-4 mb-4 flex items-center gap-2 text-black dark:text-white">
                <BarChart3 className="w-5 h-5 text-blue-500" /> Quotas & Consommation
              </h2>
              <p className="text-sm opacity-60 text-black dark:text-white">
                Suivez votre utilisation des Berrix et vérifiez votre limite quotidienne.
              </p>
              <div className="space-y-3">
                <Link 
                  to="/auth/usage/" 
                  className="flex items-center justify-between bg-blue-500/5 dark:bg-blue-500/10 p-4 rounded-xl border border-blue-500/10 hover:border-blue-500 transition-all no-underline text-black dark:text-white group"
                >
                  <span className="font-bold uppercase tracking-widest text-xs text-blue-600 dark:text-blue-400">Voir mes statistiques</span>
                  <ChevronRight className="w-5 h-5 text-blue-400 group-hover:translate-x-1 transition-all" />
                </Link>
                <Link 
                  to="/social/ai-feedback-history/" 
                  className="flex items-center justify-between bg-purple-500/5 dark:bg-purple-500/10 p-4 rounded-xl border border-purple-500/10 hover:border-purple-500 transition-all no-underline text-black dark:text-white group"
                >
                  <span className="font-bold uppercase tracking-widest text-xs text-purple-600 dark:text-purple-400">Historique des Feedbacks IA</span>
                  <ChevronRight className="w-5 h-5 text-purple-400 group-hover:translate-x-1 transition-all" />
                </Link>
              </div>
            </Card>

            {/* Portail Développeur */}
            <Card padding="lg" className="md:col-span-2 space-y-6 border-2 border-blue-500/20 bg-white dark:bg-[#0f0f1a] shadow-xl">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-6">
                  <div className="p-4 bg-blue-500/10 rounded-2xl text-blue-500">
                    <Terminal className="w-8 h-8" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold uppercase tracking-widest text-black dark:text-white mb-1">
                      Accès Développeur (API)
                    </h2>
                    <p className="text-sm text-gray-500 font-bold uppercase tracking-widest">Gérez vos clés API et accédez à la documentation technique.</p>
                  </div>
                </div>
                <Button as={Link} to="/developer/" variant="outline" className="border-blue-500/20 text-blue-500 hover:bg-blue-500/10 px-8 font-black italic manga-font text-xs">
                  TERMINAL DÉVELOPPEUR <ChevronRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AccountSettingsPage;
