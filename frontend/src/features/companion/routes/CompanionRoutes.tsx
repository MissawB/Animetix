import { Route } from 'react-router-dom';
import { lazy } from 'react';

const CompanionChatPage = lazy(() => import('../../../pages/companion/CompanionChatPage'));

export const CompanionRoutes = (
  <>
    <Route path="/companion/chat/" element={<CompanionChatPage />} />
  </>
);
