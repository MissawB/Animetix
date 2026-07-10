import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Home, RefreshCw, ServerCrash } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { ErrorPageShell } from '../../components/ui/ErrorPageShell';

const ServerErrorPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <ErrorPageShell
      code="500"
      accent="red"
      icon={<ServerCrash className="w-16 h-16 text-black" />}
      title={t('errors.server_title', 'Panne')}
      titleAccent={t('errors.server_title_accent', 'dimensionnelle')}
      description={t(
        'errors.server_desc',
        'Une anomalie a perturbé le serveur. Les techniciens du Nexus sont déjà sur le coup — réessaie dans un instant.',
      )}
      actions={
        <>
          <Button
            as="button"
            variant="primary"
            className="bg-yellow-400 !text-black border-none py-4 px-8 rounded-2xl shadow-xl hover:scale-105 transition-all font-black uppercase italic tracking-wider"
            onClick={() => window.location.reload()}
          >
            <RefreshCw className="w-5 h-5" /> {t('errors.reload', 'Recharger')}
          </Button>
          <Button
            as={Link}
            to="/"
            variant="outline"
            className="py-4 px-8 rounded-2xl font-black uppercase italic tracking-wider"
          >
            <Home className="w-5 h-5" /> {t('errors.home', 'Accueil')}
          </Button>
        </>
      }
    />
  );
};

export default ServerErrorPage;
