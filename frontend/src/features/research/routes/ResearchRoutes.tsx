import React from 'react';
import { Route } from 'react-router-dom';
import ResearchPapersPage from '../pages/ResearchPapersPage';

export const ResearchRoutes = () => (
  <>
    <Route path="/research/papers/" element={<ResearchPapersPage />} />
  </>
);
