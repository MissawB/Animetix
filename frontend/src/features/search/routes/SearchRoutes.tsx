import { Route } from 'react-router-dom';
import { lazy } from 'react';

const SearchResultsPage = lazy(() => import('../SearchResultsPage'));
const ExpertNexusPage = lazy(() => import('../ExpertNexusPage'));

export const SearchRoutes = (
  <>
    <Route path="/search/" element={<SearchResultsPage />} />
    <Route path="/search/expert/" element={<ExpertNexusPage />} />
  </>
);
