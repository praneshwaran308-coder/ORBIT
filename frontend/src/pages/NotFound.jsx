import React, { useEffect } from 'react';
import SEO from '../components/SEO';

function NotFound() {
  useEffect(() => {
    document.title = 'Page Not Found - ORBIT';
  }, []);

  return (
    <div className='p-4 min-h-screen bg-background text-on-surface flex items-center justify-center'>
      <SEO
        title='Page Not Found - ORBIT'
        description='The page you are looking for does not exist.'
        url={window.location.origin + window.location.pathname}
      />
      <section className='text-center'>
        <h1 className='text-4xl font-bold mb-4 text-primary'>404 - Page Not Found</h1>
        <p className='mb-4'>Sorry, we couldn't find that page.</p>
        <div className='flex gap-3 justify-center'>
          <a href='/' className='bg-primary text-on-primary px-4 py-2 rounded'>Home</a>
          <a href='/tasks' className='border px-4 py-2 rounded'>Start a Task</a>
        </div>
      </section>
    </div>
  );
}

export default NotFound;
