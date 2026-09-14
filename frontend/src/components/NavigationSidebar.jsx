import React from 'react';

// Simple navigation sidebar for ORBIT UI
export default function NavigationSidebar() {
  const navItems = [
    { label: 'Command Center', id: 'command-center' },
    { label: 'Tasks', id: 'tasks' },
    { label: 'Agents', id: 'agents' },
    { label: 'Activity', id: 'activity' },
    { label: 'History', id: 'history' },
    { label: 'System', id: 'system' },
    { label: 'Settings', id: 'settings' },
  ];

  return (
    <aside className="fixed top-16 left-0 w-48 h-full bg-surface-container-low overflow-y-auto p-4 shadow-inner hidden lg:block">
      <nav>
        <ul className="space-y-2">
          {navItems.map(item => (
            <li key={item.id} className="sidebar-item">
              {item.label}
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
