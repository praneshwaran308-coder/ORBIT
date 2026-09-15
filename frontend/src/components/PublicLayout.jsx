import React from 'react';
import { Outlet } from 'react-router-dom';
import Navbar from '../components/PublicNavbar';
import Footer from '../components/PublicFooter';
import Breadcrumbs from '../components/Breadcrumbs';
import CookieConsent from '../components/CookieConsent';

function PublicLayout() {
  return (
    <div className="min-h-screen flex flex-col bg-background text-on-surface">
      <Navbar />
      <main className="flex-1 p-4">
        <Breadcrumbs />
        <Outlet />
      </main>
      <CookieConsent />
      <Footer />
    </div>
  );
}

export default PublicLayout;
