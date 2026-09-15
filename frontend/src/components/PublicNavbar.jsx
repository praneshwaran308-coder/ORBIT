import React from 'react';
import { NavLink } from 'react-router-dom';

function PublicNavbar() {
  const links = [
    { to: '/', label: 'Home' },
    { to: '/about', label: 'About' },
    { to: '/faq', label: 'FAQ' },
    { to: '/contact', label: 'Contact' },
    { to: '/waitlist', label: 'Waitlist' },
    { to: '/tasks', label: 'Start a Task' },
  ];

  return (
    <nav className="bg-surface-container-high border-b border-outline-variant/30 p-4 flex flex-wrap items-center justify-between">
      <div className="flex items-center space-x-4">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end
            className={({ isActive }) =>
              `text-sm font-medium ${isActive ? 'text-primary' : 'text-on-surface'} hover:text-primary transition`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}

export default PublicNavbar;
