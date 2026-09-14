import React from 'react';

function TopBar({ task, setTask, file, setFile, loading, error, setError, handleSubmit, handleFile }) {
  return (
    <header className="fixed top-0 left-0 right-0 h-16 bg-surface-container-high flex items-center px-4 shadow-md z-10 font-inter">
      <h1 className="text-xl font-bold text-on-surface mr-4">ORBIT</h1>
      <div className="flex-1 text-sm text-on-surface opacity-70">Command Center</div>
      <div className="flex items-center space-x-4">
        <span className="text-xs text-on-surface opacity-60">Ctrl K</span>
        <button aria-label="Notifications" className="relative w-6 h-6 text-on-surface focus:outline-none">
          <svg viewBox="0 0 24 24" fill="currentColor" className="w-full h-full">
            <path d="M12 22a2 2 0 002-2h-4a2 2 0 002 2zm6-6V11c0-3.07-1.63-5.64-4.5-6.32V4a1.5 1.5 0 00-3 0v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z" />
          </svg>
        </button>
        <button aria-label="Account" className="w-8 h-8 rounded-full bg-surface-container-low flex items-center justify-center text-on-surface focus:outline-none">
          <span className="text-sm font-medium">U</span>
        </button>
      </div>
    </header>
  );
}

export default TopBar;
