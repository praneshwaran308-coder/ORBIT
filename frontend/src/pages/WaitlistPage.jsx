import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SEO from '../components/SEO';
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
function WaitlistPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, error
  const [error, setError] = useState('');

  useEffect(() => {
    document.title = 'Join the Waitlist - ORBIT';
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/waitlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Submission failed');
      }
      setStatus('idle');
      navigate('/thank-you');
    } catch (err) {
      setError(err.message);
      setStatus('error');
    }
  };

  return (
    <div className= p-4 min-h-screen bg-background text-on-surface>
      <SEO
        title=Join the Waitlist - ORBIT
        description=Sign up to be notified when ORBIT launches.
        url={window.location.origin + '/waitlist'}
      />
      <section className=max-w-2xl mx-auto>
        <h1 className=text-3xl font-bold mb-4 text-primary>Waitlist</h1>
        <p className=mb-4>Enter your email to receive updates.</p>
        <form className=space-y-4 onSubmit={handleSubmit}>
          <div>
            <label htmlFor=email className=block text-sm font-medium text-on-surface>Email</label>
            <input
              id=email
              type=email
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              className=mt-1 block w-full border rounded p-2
              placeholder=you@example.com
            />
          </div>
          {status === 'error' && <p className=text-error>{error}</p>}
          <button
            type=submit
            disabled={status === 'loading'}
            className=bg-primary text-on-primary px-4 py-2 rounded hover:bg-primary/80 transition
          >
            {status === 'loading' ? 'Submitting…' : 'Notify Me'}
          </button>
        </form>
      </section>
    </div>
  );
}

export default WaitlistPage;
