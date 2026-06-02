import { Route } from 'react-router-dom';
import { lazy } from 'react';

const LoginPage = lazy(() => import('../LoginPage'));
const RegisterPage = lazy(() => import('../RegisterPage'));
const AccountSettingsPage = lazy(() => import('../AccountSettingsPage'));

export const AuthRoutes = (
  <>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/register" element={<RegisterPage />} />
    <Route path="/settings" element={<AccountSettingsPage />} />
  </>
);
