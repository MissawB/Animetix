import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../../store/authStore';
import { socialService } from '../../features/social/services/socialService';
import { Settings, Star, ChevronRight, Sparkles, BarChart3, Terminal } from 'lucide-react';
import { useToastStore } from '../../store/toastStore';
import { Link } from 'react-router-dom';

import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { Avatar } from '../../components/ui/Avatar';
import { LAB_CTA } from '../labs/components/shared/LabKit';

const PANEL = 'rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8';
const FIELD_LABEL = 'text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5] block mb-1';
const FIELD_BOX =
  'font-bold text-lg bg-[#0B0C10] px-4 py-2 rounded-xl border border-[#F4F1E8]/10 text-[#F4F1E8]';
const H2 =
  'text-sm font-black uppercase tracking-widest border-b border-[#F4F1E8]/10 pb-4 mb-4 flex items-center gap-2 font-manga italic text-[#F4F1E8]';

const AccountSettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const { user, refetchUser } = useAuthStore();
  const { addToast } = useToastStore();

  const [customColor, setCustomColor] = useState(user?.custom_username_color || '#FFD700');
  const [isSavingColor, setIsSavingColor] = useState(false);
  const [isUploadingAvatar, setIsUploadingAvatar] = useState(false);

  const PRESET_COLORS = [
    { name: t('auth.settings.colors.sponsor_gold', 'Sponsor Or'), hex: '#FFD700' },
    { name: t('auth.settings.colors.neon_cyber', 'Néon Cyber'), hex: '#00FFCC' },
    { name: t('auth.settings.colors.sakura_pink', 'Rose Sakura'), hex: '#FF66B2' },
    { name: t('auth.settings.colors.fury_red', 'Rouge Fureur'), hex: '#FF3333' },
    { name: t('auth.settings.colors.abyss_blue', 'Bleu Abysse'), hex: '#3366FF' },
  ];

  if (!user) {
    return (
      <div className="min-h-[calc(100vh-64px)] bg-[#0B0C10] p-20 text-center text-[#F4F1E8]">
        {t('auth.settings.must_be_logged_in', 'Vous devez être connecté.')}
      </div>
    );
  }
  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      addToast(t('auth.settings.avatar_type_error', 'Le fichier doit être une image.'), 'error');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      addToast(t('auth.settings.avatar_size_error', 'Image trop lourde (max 5 Mo).'), 'error');
      return;
    }
    setIsUploadingAvatar(true);
    try {
      await socialService.uploadAvatar(file);
      await refetchUser();
      addToast(t('auth.settings.avatar_updated', 'Photo de profil mise à jour !'), 'success');
    } catch (error) {
      console.error(error);
      addToast(
        t('auth.settings.avatar_update_error', 'Erreur lors de la mise à jour de la photo.'),
        'error',
      );
    } finally {
      setIsUploadingAvatar(false);
      e.target.value = '';
    }
  };

  const handleSaveColor = async (colorToSave: string) => {
    setIsSavingColor(true);
    try {
      await socialService.updateAccountSettings({ custom_username_color: colorToSave });
      await refetchUser();
      addToast(t('auth.settings.color_updated', 'Couleur du pseudo mise à jour !'), 'success');
    } catch (error) {
      console.error(error);
      addToast(
        t('auth.settings.color_update_error', 'Erreur lors de la mise à jour de la couleur.'),
        'error',
      );
    } finally {
      setIsSavingColor(false);
    }
  };

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-4xl mx-auto px-6 py-16">
          <div className="relative mb-10 flex items-center gap-3">
            <span className="explore-stamp -rotate-2" aria-hidden>
              設
            </span>
            <span className="text-[10px] font-black uppercase tracking-[0.3em] text-[#E8442B]">
              Compte · Réglages
            </span>
          </div>
          <h1 className="text-4xl md:text-5xl font-black italic font-manga mb-12 tracking-tighter uppercase flex items-center gap-3 text-[#F4F1E8]">
            <Settings className="w-10 h-10 text-[#E8442B]" />{' '}
            {t('auth.settings.title_part1', 'GESTION DU')}{' '}
            <span className="text-[#E8442B]">{t('auth.settings.title_part2', 'COMPTE')}</span>
          </h1>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Informations générales */}
            <section className={`${PANEL} space-y-6`}>
              <h2 className={H2}>{t('auth.settings.profile', 'Profil')}</h2>
              <div className="flex items-center gap-5">
                <Avatar
                  src={user.avatar}
                  name={user.username}
                  className="h-20 w-20 rounded-2xl border border-[#F4F1E8]/10 text-2xl font-black italic"
                  fallbackClassName="bg-[#FDB913] text-[#0B0C10]"
                />
                <div className="space-y-2">
                  <span className={FIELD_LABEL}>
                    {t('auth.settings.avatar_label', 'Photo de profil')}
                  </span>
                  <label
                    className={`inline-flex cursor-pointer items-center gap-2 rounded-xl bg-[#E8442B] px-4 py-2 text-xs font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] ${
                      isUploadingAvatar ? 'pointer-events-none opacity-50' : ''
                    }`}
                  >
                    {isUploadingAvatar
                      ? t('auth.settings.avatar_uploading', 'Envoi…')
                      : t('auth.settings.avatar_change', 'Changer la photo')}
                    <input
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleAvatarChange}
                      disabled={isUploadingAvatar}
                      aria-label={t('auth.settings.avatar_label', 'Photo de profil')}
                    />
                  </label>
                  <p className="text-[10px] text-[#8F94A5]">JPG · PNG · max 5 Mo</p>
                </div>
              </div>
              <div>
                <span className={FIELD_LABEL}>
                  {t('auth.settings.username_label', "Nom d'utilisateur")}
                </span>
                <div className={FIELD_BOX}>{user.username}</div>
              </div>
              <div>
                <span className={FIELD_LABEL}>{t('auth.settings.email_label', 'Email')}</span>
                <div className={FIELD_BOX}>
                  {user.email || t('auth.settings.not_provided', 'Non renseigné')}
                </div>
              </div>
            </section>

            {/* Statut & Sponsors */}
            <section className={`${PANEL} space-y-6`}>
              <h2 className={H2}>
                <Star className="w-5 h-5 text-[#FDB913]" />{' '}
                {t('auth.settings.account_status', 'Statut du Compte')}
              </h2>
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-[#0B0C10] border border-[#F4F1E8]/10 space-y-2">
                  <span className={FIELD_LABEL}>
                    {t('auth.settings.current_status', 'Votre Statut Actuel')}
                  </span>
                  <span className="font-bold text-lg uppercase text-[#FDB913]">
                    {user.tier === 'premium'
                      ? t('auth.settings.status_boosted', 'Boosté (Sponsorisé)')
                      : t('auth.settings.status_standard', 'Standard (Financé par Pubs)')}
                  </span>
                </div>
                <p className="text-xs text-[#8F94A5] leading-relaxed">
                  {user.tier === 'premium'
                    ? t(
                        'auth.settings.boost_active_desc',
                        "Votre boost est actif. Vous profitez d'une expérience sans publicité.",
                      )
                    : t(
                        'auth.settings.standard_desc',
                        "Votre compte est actuellement en mode standard. Pour supprimer les publicités et multiplier votre quota IA par 5, visitez l'Espace Sponsors.",
                      )}
                </p>
                <Link to="/power-station/" className={`${LAB_CTA} text-xs no-underline`}>
                  {t('auth.settings.go_sponsors', "ACCÉDER À L'ESPACE SPONSORS")}
                </Link>
              </div>
            </section>

            {/* Personnalisation Cosmétique */}
            <section
              className={`${PANEL} space-y-6 relative overflow-hidden flex flex-col justify-between`}
            >
              <div>
                <h2 className={H2}>
                  <Sparkles className="w-5 h-5 text-[#FDB913]" />{' '}
                  {t('auth.settings.username_color', 'Couleur du Pseudo')}
                </h2>

                {user.unlocked_badges?.includes('Sponsor Or') ? (
                  <div className="space-y-6">
                    <p className="text-xs text-[#8F94A5]">
                      {t(
                        'auth.settings.color_desc',
                        "Personnalisez l'affichage de votre pseudo sur votre profil public.",
                      )}
                    </p>

                    {/* Preview */}
                    <div className="p-4 rounded-2xl bg-[#0B0C10] border border-[#F4F1E8]/10 text-center">
                      <span className={FIELD_LABEL}>
                        {t('auth.settings.profile_preview', 'Aperçu du Profil')}
                      </span>
                      <span
                        className="text-2xl font-black italic font-manga uppercase tracking-tighter"
                        style={{ color: customColor || undefined }}
                      >
                        {user.username}
                      </span>
                    </div>

                    {/* Presets */}
                    <div className="space-y-2">
                      <span className={FIELD_LABEL}>
                        {t('auth.settings.preset_colors', 'Couleurs Prédéfinies')}
                      </span>
                      <div className="flex flex-wrap gap-3">
                        {PRESET_COLORS.map((preset) => (
                          <button
                            key={preset.hex}
                            onClick={() => setCustomColor(preset.hex)}
                            title={preset.name}
                            aria-label={t('auth.settings.color_aria', {
                              defaultValue: 'Couleur {{name}}',
                              name: preset.name,
                            })}
                            className={`w-8 h-8 rounded-full border-2 transition-all ${
                              customColor === preset.hex
                                ? 'border-[#F4F1E8] scale-110'
                                : 'border-transparent hover:scale-105'
                            }`}
                            style={{ backgroundColor: preset.hex }}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Custom Color Picker */}
                    <div className="flex items-center gap-4">
                      <div className="space-y-1">
                        <span className={FIELD_LABEL}>
                          {t('auth.settings.custom_color', 'Couleur Personnalisée')}
                        </span>
                        <input
                          type="color"
                          aria-label={t('auth.settings.custom_color_aria', 'Couleur personnalisée')}
                          value={customColor || '#FFD700'}
                          onChange={(e) => setCustomColor(e.target.value)}
                          className="w-12 h-10 rounded-xl border border-[#F4F1E8]/15 cursor-pointer bg-transparent"
                        />
                      </div>
                      <div className="flex-1 space-y-1">
                        <span className={FIELD_LABEL}>
                          {t('auth.settings.hex_code', 'Code Hex')}
                        </span>
                        <input
                          type="text"
                          aria-label={t('auth.settings.hex_aria', 'Code hexadécimal de la couleur')}
                          value={customColor}
                          onChange={(e) => {
                            const val = e.target.value;
                            if (val === '' || val.startsWith('#')) {
                              setCustomColor(val);
                            }
                          }}
                          placeholder="#FFD700"
                          className="w-full bg-[#0B0C10] px-3 py-2 rounded-xl border border-[#F4F1E8]/10 text-sm font-mono text-[#F4F1E8] outline-none focus:border-[#FDB913] transition-colors"
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="relative py-12 text-center space-y-4">
                    <div className="mx-auto w-12 h-12 bg-[#0B0C10] border border-[#F4F1E8]/10 rounded-2xl flex items-center justify-center text-[#8F94A5]">
                      🔒
                    </div>
                    <div className="space-y-1">
                      <p className="font-bold text-sm text-[#F4F1E8]">
                        {t('auth.settings.locked_feature', 'Fonctionnalité Verrouillée')}
                      </p>
                      <p className="text-xs text-[#8F94A5] max-w-xs mx-auto">
                        {t(
                          'auth.settings.locked_desc',
                          "Soutenez Animetix dans l'Espace Sponsors pour débloquer le badge exclusif et la couleur de pseudo personnalisée !",
                        )}
                      </p>
                    </div>
                    <Link
                      to="/power-station/"
                      className="inline-block text-xs font-black uppercase tracking-wider text-[#E8442B] hover:underline no-underline"
                    >
                      {t('auth.settings.become_sponsor', 'Devenir Sponsor →')}
                    </Link>
                  </div>
                )}
              </div>

              {user.unlocked_badges?.includes('Sponsor Or') && (
                <div className="flex gap-3 pt-4 border-t border-[#F4F1E8]/10">
                  <button
                    type="button"
                    className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-6 py-2.5 font-manga text-xs font-black uppercase italic text-[#F4F1E8] transition-colors hover:bg-[#c93a24] disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
                    onClick={() => handleSaveColor(customColor)}
                    disabled={isSavingColor}
                  >
                    {isSavingColor
                      ? t('auth.settings.saving', 'Enregistrement...')
                      : t('auth.settings.save', 'Enregistrer')}
                  </button>
                  <button
                    type="button"
                    className="inline-flex items-center justify-center rounded-xl border border-[#E8442B]/40 px-5 py-2.5 text-xs font-black uppercase tracking-widest text-[#E8442B] transition-colors hover:bg-[#E8442B] hover:text-[#F4F1E8] disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={() => {
                      setCustomColor('');
                      handleSaveColor('').then();
                    }}
                    disabled={isSavingColor}
                  >
                    {t('auth.settings.reset', 'Réinitialiser')}
                  </button>
                </div>
              )}
            </section>

            {/* Historique IA */}
            <section className={`${PANEL} space-y-6`}>
              <h2 className={H2}>
                <BarChart3 className="w-5 h-5 text-[#FDB913]" />{' '}
                {t('auth.settings.quotas_title', 'Quotas & Consommation')}
              </h2>
              <p className="text-sm text-[#8F94A5]">
                {t(
                  'auth.settings.quotas_desc',
                  'Suivez votre utilisation des Berrix et vérifiez votre limite quotidienne.',
                )}
              </p>
              <div className="space-y-3">
                <Link
                  to="/auth/usage/"
                  className="flex items-center justify-between bg-[#0B0C10] p-4 rounded-xl border border-[#F4F1E8]/10 hover:border-[#FDB913] transition-colors no-underline group"
                >
                  <span className="font-black uppercase tracking-widest text-xs text-[#FDB913]">
                    {t('auth.settings.view_stats', 'Voir mes statistiques')}
                  </span>
                  <ChevronRight className="w-5 h-5 text-[#FDB913] group-hover:translate-x-1 transition-transform" />
                </Link>
                <Link
                  to="/social/ai-feedback-history/"
                  className="flex items-center justify-between bg-[#0B0C10] p-4 rounded-xl border border-[#F4F1E8]/10 hover:border-[#E8442B] transition-colors no-underline group"
                >
                  <span className="font-black uppercase tracking-widest text-xs text-[#E8442B]">
                    {t('auth.settings.ai_feedback_history', 'Historique des Feedbacks IA')}
                  </span>
                  <ChevronRight className="w-5 h-5 text-[#E8442B] group-hover:translate-x-1 transition-transform" />
                </Link>
              </div>
            </section>

            {/* Portail Développeur */}
            <section className={`${PANEL} md:col-span-2 space-y-6`}>
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-6">
                  <div className="p-4 bg-[#0B0C10] border border-[#F4F1E8]/10 rounded-2xl text-[#E8442B]">
                    <Terminal className="w-8 h-8" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold uppercase tracking-widest text-[#F4F1E8] mb-1">
                      {t('auth.settings.dev_access', 'Accès Développeur (API)')}
                    </h2>
                    <p className="text-sm text-[#8F94A5] font-bold uppercase tracking-widest">
                      {t(
                        'auth.settings.dev_desc',
                        'Gérez vos clés API et accédez à la documentation technique.',
                      )}
                    </p>
                  </div>
                </div>
                <Link
                  to="/developer/"
                  className="inline-flex items-center gap-2 rounded-xl border border-[#F4F1E8]/15 px-8 py-3 font-manga text-xs font-black uppercase italic text-[#F4F1E8] transition-colors hover:border-[#FDB913] no-underline whitespace-nowrap"
                >
                  {t('auth.settings.dev_terminal', 'TERMINAL DÉVELOPPEUR')}{' '}
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </section>
          </div>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default AccountSettingsPage;
