import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import SEO from '../components/SEO';

function HomePage() {
  const navigate = useNavigate();
  useEffect(() => {
    document.title = 'ORBIT — AI Orchestration Platform';
    const meta = document.createElement('meta');
    meta.name = 'description';
    meta.content = 'ORBIT is a powerful AI orchestration platform for building and managing automated workflows.';
    document.head.appendChild(meta);
    return () => document.head.removeChild(meta);
  }, []);

  const handleCTAClick = () => {
    navigate('/tasks');
  };

  return (
    <div className="p-4 min-h-screen bg-background text-on-surface">
      <SEO
        title="ORBIT — AI Orchestration Platform"
        description="ORBIT is a powerful AI orchestration platform for building and managing automated workflows."
        url={window.location.origin + '/'}
      />
      <section className="flex flex-col items-center justify-center py-20">
        <h1 className="text-4xl font-bold mb-6 text-primary">Welcome to ORBIT</h1>
        <p className="text-lg mb-8 max-w-2xl text-center">
          Orchestrate AI tasks effortlessly. Build, run, and monitor pipelines in a sleek, secure environment.
        </p>
        <button
          onClick={handleCTAClick}
          className="bg-primary text-on-primary px-6 py-3 rounded-md hover:bg-primary/80 transition"
        >
          Start a Task
        </button>
      </section>
    </div>
  );
}

export default HomePage;
