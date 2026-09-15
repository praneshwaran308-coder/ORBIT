import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';

function Breadcrumbs() {
  const location = useLocation();
  const pathParts = location.pathname.split('/').filter(Boolean);
  const crumbs = [{ name: 'Home', to: '/' }, ...pathParts.map((part, idx) => {
    const name = part.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    const to = '/' + pathParts.slice(0, idx + 1).join('/') + '/';
    return { name, to };
  })];
  return (
    <nav aria-label="breadcrumb" className="p-4 bg-surface-container-low">
      <ol className="flex space-x-2 text-sm text-on-surface-variant">
        {crumbs.map((c, i) => (
          <li key={c.to} className="flex items-center">
            {i > 0 && <span className="mx-2">/</span>}
            <NavLink
              to={c.to}
              className={({ isActive }) => isActive ? 'font-medium text-primary' : 'hover:text-primary'}
            >
              {c.name}
            </NavLink>
          </li>
        ))}
      </ol>
    </nav>
  );
}

export default Breadcrumbs;
