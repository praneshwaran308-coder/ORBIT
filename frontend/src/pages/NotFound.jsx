import React, { useEffect } from " react\;
import SEO from \../components/SEO\;

function NotFound() {
 useEffect(() => { document.title = 'Page Not Found — ORBIT'; }, []);
 return (
 <div className=\p-4 min-h-screen bg-background text-on-surface flex items-center justify-center\>
 <SEO
 title=\Page Not Found — ORBIT\
 description=\The page you are looking for does not exist.\
 url={window.location.origin + window.location.pathname}
 />
 <section className=\text-center\>
 <h1 className=\text-4xl font-bold mb-4 text-primary\>404 – Not Found</h1>
 <p className=\mb-4\>Sorry, we couldn’t find the page you were looking for.</p>
 <a href=\/\ className=\bg-primary text-on-primary px-4 py-2 rounded hover:bg-primary/80 transition\>Go Home</a>
 </section>
 </div>
 );
}

export default NotFound;
