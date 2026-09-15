import React, { useEffect } from 'react';

function Analytics() {
  useEffect(() => {
    const analyticsId = import.meta.env.VITE_ANALYTICS_ID;
    const consent = localStorage.getItem('cookieConsent') === 'accepted';
    if (!analyticsId || !consent) {
      return;
    }
    // Load Google Analytics script
    const script = document.createElement('script');
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${analyticsId}`;
    document.head.appendChild(script);

    const inline = document.createElement('script');
    inline.innerHTML = `window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}
gtag('js', new Date());
gtag('config', '${analyticsId}', { 'anonymize_ip': true });`;
    document.head.appendChild(inline);
  }, []);

  return null;
}

export default Analytics;
