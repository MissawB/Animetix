import { Route } from 'react-router-dom';
import { lazy } from 'react';

const MediaDetailPage = lazy(() => import('../../../pages/media/MediaDetailPage'));

export const MediaRoutes = (
  <>
    <Route path="/media/:mediaId/" element={<MediaDetailPage />} />
  </>
);
