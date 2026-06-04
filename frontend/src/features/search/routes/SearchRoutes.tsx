import { Route } from 'react-router-dom';
import { lazy } from 'react';

const SearchResultsPage = lazy(() => import('../SearchResultsPage'));
const ExpertNexusPage = lazy(() => import('../ExpertNexusPage'));
const CounterfactualSimulatorPage = lazy(() => import('../CounterfactualSimulatorPage'));
const UniversalSearchHubPage = lazy(() => import('../UniversalSearchHubPage'));

export const SearchRoutes = (
  <>
    <Route path="/search/" element={<UniversalSearchHubPage />} />
    <Route path="/search/results/" element={<SearchResultsPage />} />
    <Route path="/search/expert/" element={<ExpertNexusPage />} />
    <Route path="/search/counterfactual/" element={<CounterfactualSimulatorPage />} />
  </>
);
