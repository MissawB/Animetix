import { Route } from 'react-router-dom';
import { lazy } from 'react';

const ExplorePage = lazy(() => import('../../../pages/explore/ExplorePage'));
const SeichijunreiMapPage = lazy(() => import('../../../pages/explore/SeichijunreiMapPage'));

export const ExploreRoutes = (
  <>
    <Route path="/explore/" element={<ExplorePage />} />
    <Route path="/explore/seichijunrei/" element={<SeichijunreiMapPage />} />
  </>
);
