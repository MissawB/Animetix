import { Route } from 'react-router-dom';
import { lazy } from 'react';

const MediaDetailPage = lazy(() => import('../MediaDetailPage'));

export const MediaRoutes = (
  <>
    <Route path="/media/:mediaType/:itemId/" element={<MediaDetailPage />} />
  </>
);
