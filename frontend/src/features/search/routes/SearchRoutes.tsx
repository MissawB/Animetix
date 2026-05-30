import { Route } from 'react-router-dom';
import { lazy } from 'react';

const SearchResultsPage = lazy(() => import('../SearchResultsPage'));

export const SearchRoutes = (
  <>
    <Route path="/search/" element={<SearchResultsPage />} />
  </>
);
