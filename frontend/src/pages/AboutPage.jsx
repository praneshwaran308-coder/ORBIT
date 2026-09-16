import React, { useEffect } from 'react';
import SEO from '../components/SEO';
import Reviews from '../components/Reviews';

function AboutPage() {
  useEffect(() => {
    document.title = 'About ORBIT';
  }, []);

  return (
    <div className="p-4 min-h-screen bg-background text-on-surface">
      <SEO
        title="About ORBIT"
        description="Learn about the ORBIT AI orchestration platform and its capabilities."
        url={window.location.origin + '/about'}
      />
      <section className="max-w-2xl mx-auto">
      
        <h1 className="text-3xl font-bold mb-4 text-primary">About ORBIT</h1>
        <p className="mb-4">ORBIT is a powerful AI orchestration platform that lets you build, run, and monitor automated workflows in a secure, scalable environment.</p>
        <p className="mb-4">The platform currently uses an in‑memory TaskRegistry. See the documentation for data isolation details.</p>
        </section>
      <Reviews />
    </div>
  );
}

export default AboutPage;
