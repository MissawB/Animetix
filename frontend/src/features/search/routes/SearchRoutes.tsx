import { Route } from 'react-router-dom';
import { lazy } from 'react';

const SearchResultsPage = lazy(() => import('../../../pages/search/SearchResultsPage'));
const ExpertNexusPage = lazy(() => import('../../../pages/search/ExpertNexusPage'));
const CounterfactualSimulatorPage = lazy(() => import('../../../pages/search/CounterfactualSimulatorPage'));
const UniversalSearchHubPage = lazy(() => import('../../../pages/search/UniversalSearchHubPage'));

export const SearchRoutes = () => (
  <>
    <Route path="/search/" element={<UniversalSearchHubPage />} />
    <Route path="/search/results/" element={<SearchResultsPage />} />
    <Route path="/search/expert-nexus/" element={<ExpertNexusPage />} />
    <Route path="/search/counterfactual/" element={<CounterfactualSimulatorPage />} />
  </>
);
