import React from 'react';

function Sidebar({ history, expandedRows, toggleRow }) {
  return (
    <aside className="fixed top-16 left-0 w-56 h-full bg-surface-container-low overflow-y-auto p-4 shadow-inner hidden lg:block">
      <h2 className="text-sm font-bold text-on-surface mb-2">History</h2>
      <ul className="space-y-2">
        {history.map((run) => {
          const isError = run.status === 'failed';
          const isExpanded = expandedRows[run.id];
          return (
            <li key={run.id} className="bg-surface-container border border-outline-variant/30 rounded p-2 cursor-pointer" onClick={() => toggleRow(run.id)}>
              <div className="flex justify-between items-center">
                <span className="font-body-sm text-on-surface truncate">{run.description}</span>
                <span className={`font-body-sm ${isError ? 'text-error' : 'text-primary'}`}>{isError ? 'Failed' : 'Done'}</span>
              </div>
              {isExpanded && (
                <pre className="mt-2 text-xs whitespace-pre-wrap text-outline">{JSON.stringify(run.result, null, 2)}</pre>
              )}
            </li>
          );
        })}
      </ul>
    </aside>
  );
}

export default Sidebar;
