import React, { useEffect } from  react;
import SEO from ../components/SEO;

function ThankYouPage() {
  useEffect(() => { document.title = 'Thank You — ORBIT'; }, []);
  return (
    <div className=\p-4 min-h-screen bg-background text-on-surface\>
      <SEO
        title=\Thank You — ORBIT\
        description=\Thank you for using ORBIT. Your action was successful.\
        url={window.location.origin + '/thank-you'}
      />
      <section className=\max-w-2xl mx-auto\>
        <h1 className=\text-3xl font-bold mb-4 text-primary\>Thank You!</h1>
        <p className=\mb-4\>Your submission has been received. We will get back to you shortly.</p>
      </section>
    </div>
  );
}

export default ThankYouPage;
