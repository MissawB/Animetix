import React from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, MessageSquare, Clock } from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { Link } from 'react-router-dom';

const CONTACT_EMAIL = 'missaw.redfox@gmail.com';

/**
 * Page "Contact" — page publique requise (AdSense : moyen de contact visible).
 * Texte FR par défaut inline; traductions EN dans les fragments i18n (legal.*).
 */
const ContactPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <AnimatedPage>
      <div className="min-h-[calc(100vh-64px)] bg-[#0B0C10] text-[#F4F1E8]">
        <div className="max-w-2xl mx-auto px-6 py-16">
          <header className="mb-10 text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[#E8442B]/25 bg-[#E8442B]/10 text-[#E8442B] text-[10px] font-black uppercase tracking-[0.25em] mb-5">
              <MessageSquare className="w-4 h-4" /> {t('legal.contact.badge', 'Contact')}
            </div>
            <h1 className="text-4xl md:text-5xl font-black italic font-manga tracking-tighter uppercase mb-4 text-[#F4F1E8]">
              {t('legal.contact.title', 'Contactez-nous')}
            </h1>
            <p className="text-base text-[#8F94A5] font-bold leading-relaxed">
              {t(
                'legal.contact.intro',
                'Une question, un bug, une demande relative à vos données personnelles ou un partenariat ? Écrivez-nous, nous répondons à chaque message.',
              )}
            </p>
          </header>

          <section className="rounded-2xl border border-[#F4F1E8]/10 bg-[#0F1016] p-6 sm:p-8 space-y-6 text-center">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-[#E8442B]/10 text-[#E8442B] flex items-center justify-center">
              <Mail className="w-7 h-7" />
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-[#8F94A5]">
                {t('legal.contact.email_label', 'Adresse e-mail')}
              </p>
              <a
                href={`mailto:${CONTACT_EMAIL}`}
                className="text-lg md:text-xl font-black text-[#FDB913] underline hover:text-[#E8442B] break-all"
              >
                {CONTACT_EMAIL}
              </a>
            </div>

            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-[#E8442B] px-8 py-4 font-manga text-base font-black uppercase italic text-[#F4F1E8] no-underline transition-colors hover:bg-[#c93a24] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FDB913]"
            >
              {t('legal.contact.cta', 'Envoyer un e-mail')}
            </a>

            <p className="text-xs text-[#8F94A5] font-bold inline-flex items-center justify-center gap-2 pt-2">
              <Clock className="w-3.5 h-3.5" />
              {t('legal.contact.response', 'Délai de réponse habituel : sous 48 heures.')}
            </p>
          </section>

          <p className="text-center text-xs text-[#8F94A5] font-bold mt-6">
            {t('legal.contact.privacy_note', 'Vos échanges sont traités conformément à notre')}{' '}
            <Link to="/privacy/" className="text-[#FDB913] underline hover:text-[#E8442B]">
              {t('nav.privacy', 'Politique de confidentialité')}
            </Link>
            .
          </p>
        </div>
      </div>
    </AnimatedPage>
  );
};

export default ContactPage;
