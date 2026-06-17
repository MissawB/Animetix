import { Route } from 'react-router-dom';
import { lazy } from 'react';

const DailyChallengePage = lazy(() => import('../../../pages/utils/DailyChallengePage'));
const CustomConfigPage = lazy(() => import('../../../pages/utils/CustomConfigPage'));
const ArchetypeGuidePage = lazy(() => import('../../../pages/utils/ArchetypeGuidePage'));

export const UtilsRoutes = () => (
  <>
    <Route path="/daily-challenge/" element={<DailyChallengePage />} />
    <Route path="/custom-config/" element={<CustomConfigPage />} />
    <Route path="/guide/archetypes/" element={<ArchetypeGuidePage />} />
  </>
);
