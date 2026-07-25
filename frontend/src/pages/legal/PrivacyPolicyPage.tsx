import React from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, Mail } from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';

const CONTACT_EMAIL = 'missaw.redfox@gmail.com';

/**
 * Politique de confidentialité — page publique requise (AdSense + RGPD).
 * Déclare l'usage des cookies publicitaires Google/AdSense et les droits RGPD.
 * Le texte français est le défaut inline de t(); les traductions EN vivent dans
 * les fragments i18n (legal.*).
 */
const PrivacyPolicyPage: React.FC = () => {
  const { t } = useTranslation();

  const sections: { title: string; paragraphs: string[] }[] = [
    {
      title: t('legal.privacy.s_data.title', 'Données que nous collectons'),
      paragraphs: [
        t(
          'legal.privacy.s_data.p1',
          "Lorsque vous créez un compte, nous traitons votre adresse e-mail et un identifiant d'authentification (via Google Identity / Firebase). Pendant votre navigation, nous conservons vos préférences de jeu, votre historique de parties, votre solde de Berrix et les contenus que vous générez dans les Labs.",
        ),
        t(
          'legal.privacy.s_data.p2',
          "Des données techniques (adresse IP, type d'appareil, pages consultées) sont enregistrées pour la sécurité, la limitation de débit et la mesure d'audience.",
        ),
      ],
    },
    {
      title: t('legal.privacy.s_ads.title', 'Cookies et publicité (Google AdSense)'),
      paragraphs: [
        t(
          'legal.privacy.s_ads.p1',
          "Ce site affiche des annonces fournies par Google AdSense. Google et ses partenaires utilisent des cookies pour diffuser des annonces en fonction de vos visites sur ce site et sur d'autres sites Internet.",
        ),
        t(
          'legal.privacy.s_ads.p2',
          'Les cookies publicitaires (notamment le cookie DoubleClick) permettent à Google et à ses partenaires de personnaliser les annonces. Vous pouvez désactiver la publicité personnalisée en visitant les Paramètres des annonces Google (adssettings.google.com), ou refuser les cookies tiers via www.aboutads.info/choices.',
        ),
        t(
          'legal.privacy.s_ads.p3',
          "Dans l'Espace économique européen, un bandeau de consentement recueille votre choix avant tout dépôt de cookie publicitaire non essentiel. Vous pouvez modifier ou retirer ce consentement à tout moment depuis les paramètres du site.",
        ),
      ],
    },
    {
      title: t('legal.privacy.s_third.title', 'Services tiers'),
      paragraphs: [
        t(
          'legal.privacy.s_third.p1',
          "Nous nous appuyons sur des sous-traitants qui traitent certaines données pour notre compte : Google AdSense (publicité), Google/Firebase (authentification), ainsi que des fournisseurs d'inférence IA pour les fonctionnalités des Labs. Chacun applique sa propre politique de confidentialité. Nous ne vendons pas vos données personnelles.",
        ),
      ],
    },
    {
      title: t('legal.privacy.s_rights.title', 'Vos droits (RGPD)'),
      paragraphs: [
        t(
          'legal.privacy.s_rights.p1',
          "Conformément au RGPD, vous disposez d'un droit d'accès, de rectification, d'effacement, de limitation, de portabilité et d'opposition sur vos données personnelles. Vous pouvez exercer ces droits, ou retirer votre consentement, en nous contactant à l'adresse ci-dessous.",
        ),
        t(
          'legal.privacy.s_rights.p2',
          'Nous conservons vos données aussi longtemps que votre compte est actif, puis pendant la durée légale applicable. Vous pouvez demander la suppression de votre compte à tout moment.',
        ),
      ],
    },
  ];

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-3xl mx-auto px-6 py-16">
          <header className="mb-10">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#E8442B]/25 bg-[#E8442B]/10 text-[#E8442B] text-[10px] font-black uppercase tracking-[0.25em] mb-5">
              <ShieldCheck className="w-4 h-4" /> {t('legal.privacy.badge', 'Confidentialité')}
            </div>
            <div className="flex items-center gap-3 mb-3">
              <span className="explore-stamp -rotate-2" aria-hidden>
                密
              </span>
              <h1 className="text-4xl md:text-5xl font-black italic font-manga tracking-tighter uppercase text-[#F4F1E8]">
                {t('legal.privacy.title', 'Politique de confidentialité')}
              </h1>
            </div>
            <p className="text-sm text-[#8F94A5] font-bold">
              {t('legal.privacy.updated', 'Dernière mise à jour : juillet 2026')}
            </p>
          </header>

          <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8 space-y-8">
            <p className="text-base leading-relaxed text-[#F4F1E8]/80">
              {t(
                'legal.privacy.intro',
                "Cette politique explique quelles données personnelles Animetix collecte, pourquoi, et comment nous les protégeons — y compris l'usage des cookies publicitaires.",
              )}
            </p>

            {sections.map((section) => (
              <section key={section.title} className="space-y-3">
                <h2 className="text-lg font-black uppercase tracking-wide font-manga italic text-[#E8442B]">
                  {section.title}
                </h2>
                {section.paragraphs.map((p, i) => (
                  <p key={i} className="text-sm leading-relaxed text-[#8F94A5]">
                    {p}
                  </p>
                ))}
              </section>
            ))}

            <section className="space-y-3 pt-2 border-t border-[#F4F1E8]/10">
              <h2 className="text-lg font-black uppercase tracking-wide font-manga italic text-[#E8442B]">
                {t('legal.privacy.s_contact.title', 'Nous contacter')}
              </h2>
              <p className="text-sm leading-relaxed text-[#8F94A5] inline-flex items-center gap-2">
                <Mail className="w-4 h-4 shrink-0" />
                <a
                  href={`mailto:${CONTACT_EMAIL}`}
                  className="font-bold text-[#FDB913] underline hover:text-[#E8442B]"
                >
                  {CONTACT_EMAIL}
                </a>
              </p>
            </section>
          </section>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default PrivacyPolicyPage;
