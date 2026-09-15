import React, { useState, useEffect } from 'react';

function CookieConsent() {
 const [visible, setVisible] = useState(false);
 const analyticsId = import.meta.env.VITE_ANALYTICS_ID;

 useEffect(() => {
  const analyticsId = import.meta.env.VITE_ANALYTICS_ID;
  if (!analyticsId) return; // No analytics configured, no consent needed
  const consent = localStorage.getItem('cookieConsent');
  if (!consent) {
   setVisible(true);
  }
 }, [analyticsId]);

 const accept = () => {
 localStorage.setItem('cookieConsent', 'accepted');
 setVisible(false);
 };

 const decline = () => {
 localStorage.setItem('cookieConsent', 'declined');
 setVisible(false);
 };

 if (!visible) return null;

 return (
 <div className=\fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-surface-container-highest text-on-surface p-4 rounded shadow-lg max-w-md w-full flex flex-col md:flex-row items-center md:items-start space-y-2 md:space-y-0 md:space-x-4\>
 <p className=\flex-1 text-sm\>
 We use cookies to improve your experience, analyze traffic, and personalize content. By clicking \Accept\, you agree to our use of cookies.
 </p>
 <div className=\flex space-x-2\>
 <button onClick={accept} className=\bg-primary text-on-primary px-3 py-1 rounded hover:bg-primary/80 transition\>Accept</button>
 <button onClick={decline} className=\bg-surface-container text-on-surface px-3 py-1 rounded hover:bg-surface-container-low transition\>Decline</button>
 </div>
 </div>
 );
}

export default CookieConsent;
