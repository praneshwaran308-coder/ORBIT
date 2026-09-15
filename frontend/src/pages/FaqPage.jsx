import React, { useEffect } from 'react';
import SEO from '../components/SEO';

function FaqPage() {
  // SEO handled via component
  return (
    <div className="p-4 min-h-screen bg-background text-on-surface">
      <SEO
        title="FAQ — ORBIT"
        description="Frequently asked questions about ORBIT AI orchestration platform."
        url={window.location.origin + '/faq'}
      />
      <section className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-4 text-primary">Frequently Asked Questions</h1>
        <dl className="space-y-4">
          <div>
            <dt className="font-medium text-primary">What is ORBIT?</dt>
            <dd className="mt-1 text-on-surface-variant">ORBIT is an AI orchestration platform that lets you build, run, and monitor automated workflows.</dd>
          </div>
          <div>
            <dt className="font-medium text-primary">Is there a free tier?</dt>
            <dd className="mt-1 text-on-surface-variant">Yes, a generous free tier is available for small projects and experimentation.</dd>
          </div>
          {/* Add more FAQ items as needed */}
        </dl>
      </section>
    </div>
  );
}

export default FaqPage;
