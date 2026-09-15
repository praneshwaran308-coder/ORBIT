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
          <Route path="/" element={<PublicLayout><HomePage /></PublicLayout>} />
          <Route path="/about" element={<PublicLayout><AboutPage /></PublicLayout>} />
          <Route path="/faq" element={<PublicLayout><FaqPage /></PublicLayout>} />
          <Route path="/contact" element={<PublicLayout><ContactPage /></PublicLayout>} />
          <Route path="/waitlist" element={<PublicLayout><WaitlistPage /></PublicLayout>} />
          <Route path="/thank-you" element={<PublicLayout><ThankYouPage /></PublicLayout>} />
          {/* Catch‑all 404 */}
          <Route path="*" element={<PublicLayout><NotFound /></PublicLayout>} />
        </Routes>
      </BrowserRouter>
    </ExecutionProvider>
  );
}

export default App;
