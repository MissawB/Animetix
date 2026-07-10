import { Route } from 'react-router-dom';
import { lazy } from 'react';

const DailyChallengePage = lazy(() => import('../../../pages/utils/DailyChallengePage'));
const CustomConfigPage = lazy(() => import('../../../pages/utils/CustomConfigPage'));
const ArchetypeGuidePage = lazy(() => import('../../../pages/utils/ArchetypeGuidePage'));
const ForbiddenPage = lazy(() => import('../../../pages/utils/ForbiddenPage'));
const ServerErrorPage = lazy(() => import('../../../pages/utils/ServerErrorPage'));

export const UtilsRoutes = () => (
  <>
    <Route path="/daily-challenge/" element={<DailyChallengePage />} />
    <Route path="/custom-config/" element={<CustomConfigPage />} />
    <Route path="/guide/archetypes/" element={<ArchetypeGuidePage />} />
    {/* Pages d'erreur adressables (redirections, liens depuis les gardes/toasts). */}
    <Route path="/error/403/" element={<ForbiddenPage />} />
    <Route path="/error/500/" element={<ServerErrorPage />} />
  </>
);
