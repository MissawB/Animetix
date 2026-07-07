import { Route } from 'react-router-dom';
import { lazy } from 'react';

const PrivacyPolicyPage = lazy(() => import('../../../pages/legal/PrivacyPolicyPage'));
const AboutPage = lazy(() => import('../../../pages/legal/AboutPage'));
const ContactPage = lazy(() => import('../../../pages/legal/ContactPage'));

export const LegalRoutes = () => (
  <>
    <Route path="/privacy/" element={<PrivacyPolicyPage />} />
    <Route path="/about/" element={<AboutPage />} />
    <Route path="/contact/" element={<ContactPage />} />
  </>
);
