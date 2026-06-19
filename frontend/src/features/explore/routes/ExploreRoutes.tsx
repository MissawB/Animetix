import { Route } from 'react-router-dom';
import { lazy } from 'react';

const ExplorePage = lazy(() => import('../../../pages/explore/ExplorePage'));
const SeichijunreiMapPage = lazy(() => import('../../../pages/explore/SeichijunreiMapPage'));
const MarketWikiPage = lazy(() => import('../../../pages/explore/MarketWikiPage'));
const ShopPage = lazy(() => import('../../../pages/explore/ShopPage'));

export const ExploreRoutes = () => (
  <>
    <Route path="/explore/" element={<ExplorePage />} />
    <Route path="/explore/seichijunrei/" element={<SeichijunreiMapPage />} />
    <Route path="/explore/market/" element={<MarketWikiPage />} />
    <Route path="/explore/shop/" element={<ShopPage />} />
  </>
);
