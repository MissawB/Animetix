import React from 'react';
import { useTranslation } from 'react-i18next';
import { Mail, MessageSquare, Clock } from 'lucide-react';
import { AnimatedPage } from '../../components/ui/AnimatedPage';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
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
      <div className="max-w-2xl mx-auto px-6 py-16">
        <header className="mb-10 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-primary/10 text-brand-primary text-[10px] font-black uppercase tracking-[0.25em] mb-5">
            <MessageSquare className="w-4 h-4" /> {t('legal.contact.badge', 'Contact')}
          </div>
          <h1 className="text-4xl md:text-5xl font-black italic tracking-tighter uppercase mb-4">
            {t('legal.contact.title', 'Contactez-nous')}
          </h1>
          <p className="text-base opacity-70 font-bold leading-relaxed">
            {t(
              'legal.contact.intro',
              'Une question, un bug, une demande relative à vos données personnelles ou un partenariat ? Écrivez-nous, nous répondons à chaque message.',
            )}
          </p>
        </header>

        <Card padding="lg" className="space-y-6 text-center">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-brand-primary/10 text-brand-primary flex items-center justify-center">
            <Mail className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <p className="text-xs font-black uppercase tracking-widest opacity-50">
              {t('legal.contact.email_label', 'Adresse e-mail')}
            </p>
            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="text-lg md:text-xl font-black underline hover:text-brand-primary break-all"
            >
              {CONTACT_EMAIL}
            </a>
          </div>

          <a href={`mailto:${CONTACT_EMAIL}`} className="inline-block">
            <Button variant="primary" className="mx-auto">
              {t('legal.contact.cta', 'Envoyer un e-mail')}
            </Button>
          </a>

          <p className="text-xs opacity-60 font-bold inline-flex items-center justify-center gap-2 pt-2">
            <Clock className="w-3.5 h-3.5" />
            {t('legal.contact.response', 'Délai de réponse habituel : sous 48 heures.')}
          </p>
        </Card>

        <p className="text-center text-xs opacity-50 font-bold mt-6">
          {t('legal.contact.privacy_note', 'Vos échanges sont traités conformément à notre')}{' '}
          <Link to="/privacy/" className="underline hover:text-brand-primary">
            {t('nav.privacy', 'Politique de confidentialité')}
          </Link>
          .
        </p>
      </div>
    </AnimatedPage>
  );
};

export default ContactPage;
