import { Route } from 'react-router-dom';
import { lazy } from 'react';

const ExplorePage = lazy(() => import('../../../pages/explore/ExplorePage'));

export const ExploreRoutes = (
  <>
    <Route path="/explore/" element={<ExplorePage />} />
  </>
);
