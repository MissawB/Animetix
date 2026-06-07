import { Route } from 'react-router-dom';
import { lazy } from 'react';

const LoginPage = lazy(() => import('../../../pages/auth/LoginPage'));
const RegisterPage = lazy(() => import('../../../pages/auth/RegisterPage'));
const AccountSettingsPage = lazy(() => import('../../../pages/auth/AccountSettingsPage'));

export const AuthRoutes = (
  <>
    <Route path="/auth/login/" element={<LoginPage />} />
    <Route path="/auth/register/" element={<RegisterPage />} />
    <Route path="/auth/settings/" element={<AccountSettingsPage />} />
  </>
);
