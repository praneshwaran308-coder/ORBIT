import React from 'react';
import AboutPage from './pages/AboutPage';
import FaqPage from './pages/FaqPage';
import ContactPage from './pages/ContactPage';
import WaitlistPage from './pages/WaitlistPage';
import ThankYouPage from './pages/ThankYouPage';
import NotFound from './pages/NotFound';
import HomePage from './pages/HomePage';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ExecutionProvider } from './context/ExecutionContext';
import AppShell from './components/AppShell';
import PublicLayout from './components/PublicLayout';

function App() {
  return (
    <ExecutionProvider>
      <BrowserRouter>
        <Routes>
          {/* Application routes retaining existing UI */}
          <Route path="/tasks/*" element={<AppShell />} />
          <Route path="/agents/*" element={<AppShell />} />
          <Route path="/activity/*" element={<AppShell />} />
          <Route path="/history/*" element={<AppShell />} />
          <Route path="/settings/*" element={<AppShell />} />
          {/* Public pages */}
          <Route element={<PublicLayout />}>
            <Route index element={<HomePage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="faq" element={<FaqPage />} />
            <Route path="contact" element={<ContactPage />} />
            <Route path="waitlist" element={<WaitlistPage />} />
            <Route path="thank-you" element={<ThankYouPage />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ExecutionProvider>
  );
}

export default App;
