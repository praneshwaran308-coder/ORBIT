import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SEO from '../components/SEO';
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
function ContactPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({ name: '', email: '', message: '' });
  const [status, setStatus] = useState('idle'); // idle, loading, error
  const [error, setError] = useState('');

  useEffect(() => {
    document.title = 'Contact - ORBIT';
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.id]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setError('');
    try {
      const res = await fetch(`${API_BASE_URL}/api/contact`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
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
        title=Contact - ORBIT
        description=Get in touch with the ORBIT team for support or inquiries.
        url={window.location.origin + '/contact'}
      />
      <section className=max-w-2xl mx-auto>
        <h1 className=text-3xl font-bold mb-4 text-primary>Contact Us</h1>
        <p className=mb-4>We would love to hear from you. Please fill out the form below.</p>
        <form className=space-y-4 onSubmit={handleSubmit}>
          <div>
            <label htmlFor=name className=block text-sm font-medium text-on-surface>Name</label>
            <input
              id=name
              type=text
              required
              value={formData.name}
              onChange={handleChange}
              className=mt-1 block w-full border rounded p-2
              placeholder=Your name
            />
          </div>
          <div>
            <label htmlFor=email className=block text-sm font-medium text-on-surface>Email</label>
            <input
              id=email
              type=email
              required
              value={formData.email}
              onChange={handleChange}
              className=mt-1 block w-full border rounded p-2
              placeholder=you@example.com
            />
          </div>
          <div>
            <label htmlFor=message className=block text-sm font-medium text-on-surface>Message</label>
            <textarea
              id=message
              rows={4}
              required
              value={formData.message}
              onChange={handleChange}
              className=mt-1 block w-full border rounded p-2
              placeholder=Your message
            />
          </div>
          {status === 'error' && <p className=text-error>{error}</p>}
          <button
            type=submit
            disabled={status === 'loading'}
            className=bg-primary text-on-primary px-4 py-2 rounded hover:bg-primary/80 transition
          >
            {status === 'loading' ? 'Sending…' : 'Send Message'}
          </button>
        </form>
      </section>
    </div>
  );
}

export default ContactPage;
