import { useEffect } from 'react';

function SEO({ title, description, url, image }) {
  useEffect(() => {
    if (title) document.title = title;
    const setMeta = (name, content) => {
      let element = document.querySelector(`meta[name="${name}"]`);
      if (!element) {
        element = document.createElement('meta');
        element.setAttribute('name', name);
        document.head.appendChild(element);
      }
      element.setAttribute('content', content);
    };
    if (description) setMeta('description', description);
    if (url) setMeta('canonical', url);
    // Open Graph
    if (title) setMeta('og:title', title);
    if (description) setMeta('og:description', description);
    if (url) setMeta('og:url', url);
    if (image) setMeta('og:image', image);
  }, [title, description, url, image]);
  return null;
}

export default SEO;
