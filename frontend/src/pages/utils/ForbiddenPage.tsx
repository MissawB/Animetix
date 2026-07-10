import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Home, ArrowLeft, ShieldAlert } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { ErrorPageShell } from '../../components/ui/ErrorPageShell';

const ForbiddenPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <ErrorPageShell
      code="403"
      accent="orange"
      icon={<ShieldAlert className="w-16 h-16 text-black" />}
      title={t('errors.forbidden_title', 'Zone')}
      titleAccent={t('errors.forbidden_title_accent', 'interdite')}
      description={t(
        'errors.forbidden_desc',
        "Cette dimension est réservée aux administrateurs du Nexus. Ton compte n'a pas les autorisations requises.",
      )}
      actions={
        <>
          <Button
            as={Link}
            to="/"
            variant="primary"
            className="bg-yellow-400 !text-black border-none py-4 px-8 rounded-2xl shadow-xl hover:scale-105 transition-all font-black uppercase italic tracking-wider"
          >
            <Home className="w-5 h-5" /> {t('errors.home', 'Accueil')}
          </Button>
          <Button
            as="button"
            variant="outline"
            className="py-4 px-8 rounded-2xl font-black uppercase italic tracking-wider"
            onClick={() => window.history.back()}
          >
            <ArrowLeft className="w-5 h-5" /> {t('errors.back', 'Retour')}
          </Button>
        </>
      }
    />
  );
};

export default ForbiddenPage;
