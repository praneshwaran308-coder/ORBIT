import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useExecution } from '../context/ExecutionContext';
import TopBar from './TopBar';
import NavigationSidebar from './NavigationSidebar';
import ExecutionGraph from './ExecutionGraph';
import { formatNumber, sanitizeText } from '../utils/helpers';
import { runTask as apiRunTask, getStatus as apiGetStatus } from '../api/execution';

function AppShell() {
  const { state, startTask, updateAgent, logEvent, completeTask, failTask } = useExecution();
  const [task, setTask] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activity, setActivity] = useState([]);
  const [showCmdK, setShowCmdK] = useState(false);
  const [cmdKTask, setCmdKTask] = useState('');
  const [showExecAnimation, setShowExecAnimation] = useState(false);
  const [expandedRows, setExpandedRows] = useState({});
  const requestIdRef = useRef(0);
  const cmdKInputRef = useRef(null);

  // Command Palette shortcuts
  useEffect(() => {
    document.documentElement.classList.add('dark');
    const handler = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowCmdK((prev) => !prev);
      }
      if (e.key === 'Escape' && showCmdK) setShowCmdK(false);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [showCmdK]);

  useEffect(() => {
    if (showCmdK && cmdKInputRef.current) cmdKInputRef.current.focus();
  }, [showCmdK]);

  const generateTaskId = () => `ORB-${Math.random().toString(36).substr(2, 5).toUpperCase()}`;

  const runTask = async (overrideTask = null, overrideFile = null) => {
    const taskText = overrideTask !== null ? overrideTask : task;
    const trimmedTask = taskText.trim();
    const currentFile = overrideFile !== null ? overrideFile : file;
    if (!trimmedTask && !currentFile) {
      setError('Please enter a task or attach a dataset.');
      return;
    }
    if (showCmdK) {
      setShowCmdK(false);
      setCmdKTask('');
    }
    setTask(trimmedTask);
    setLoading(true);
    setError('');
    try {
      // Use API client
      const runResponse = await apiRunTask(trimmedTask, currentFile ? currentFile.name : null);
      console.log('POST /run response:', runResponse);
      const backendTaskId = runResponse.task_id;
      startTask(backendTaskId, trimmedTask || (currentFile ? currentFile.name : 'System Task'));
      // Initial activity from response if any
      if (Array.isArray(runResponse.activity)) {
        setActivity(runResponse.activity.map((a) => ({ text: a.message, status: a.status || 'active' })));
      }
      // Poll for status every 800ms
      const interval = setInterval(async () => {
        try {
          const statusData = await apiGetStatus(backendTaskId);
          console.log(`GET /status/${backendTaskId} response:`, statusData);
          // Dispatch activity events
          if (Array.isArray(statusData.activity)) {
            setActivity(statusData.activity.map((a) => ({ text: a.message, status: a.status || 'active' })));
            // also log each activity to context
            statusData.activity.forEach((act) => {
              logEvent(backendTaskId, act.source || 'SYSTEM', act.message, act.status || 'active');
            });
          }
          // Update agents if present
          if (Array.isArray(statusData.agents)) {
            statusData.agents.forEach((agent) => {
              // Assuming agent object has name and status fields
              updateAgent(backendTaskId, agent.name, agent.status);
            });
          }
          if (statusData.status === 'completed') {
            completeTask(backendTaskId, statusData.result);
            setLoading(false);
            clearInterval(interval);
          } else if (statusData.status === 'failed') {
            failTask(backendTaskId, statusData.error || 'Task failed');
            setError(statusData.error || 'Task failed');
            setLoading(false);
            clearInterval(interval);
          }
        } catch (e) {
          console.error('Polling error', e);
          // optional: could fail task here
        }
      }, 800);
    } catch (e) {
      console.error('Run task error', e);
      setError('Failed to start task.');
      setLoading(false);
    }
  };

  const handleCenterSubmit = (e) => { e.preventDefault(); runTask(); };
  const handleCmdKSubmit = (e) => { e.preventDefault(); if (!cmdKTask.trim()) return; runTask(cmdKTask, null); };
  const handleFileChange = (e) => { const f = e.target.files?.[0] || null; if (f) setFile(f); };
  const toggleRow = (id) => setExpandedRows((p) => ({ ...p, [id]: !p[id] }));
  const getAgentTextColor = (name) => {
    switch (name) {
      case 'Research Agent': return 'text-primary';
      case 'Data Agent': return 'text-secondary';
      case 'ML Agent': return 'text-tertiary';
      default: return 'text-outline';
    }
  };

  const renderOperationStrip = () => (
    <div className="telemetry-strip">
      {[{ label: 'ACTIVE RUNS', value: loading ? '1' : '0', context: loading ? 'Executing pipeline' : 'No active executions' },{ label: 'QUEUE', value: '0', context: 'Ready for dispatch' },{ label: 'P99 LATENCY', value: '1.2s', context: 'Last 20 executions' },{ label: 'AGENTS', value: '3 / 3', context: 'All systems available' },].map((m, i) => (
        <div key={i} className="telemetry-item">
          <span className="telemetry-label">{m.label}</span>
          <span className="telemetry-value">{m.value}</span>
          <span className="telemetry-context">{m.context}</span>
        </div>
      ))}
    </div>
  );

  const renderEmptyState = () => (
    <div className="py-12 text-center text-outline font-body-sm bg-surface-container-low rounded border border-outline-variant/30 border-dashed">
      <p className="font-headline-sm font-medium text-on-surface mb-2">No executions yet</p>
      <p className="mb-4">Start a task above and ORBIT will automatically route it.</p>
      <div className="flex gap-4 justify-center">
        <button className="px-3 py-1 bg-surface-container-high rounded hover:bg-surface-container-highest transition-colors" onClick={() => setTask('Research a topic')}>Research a topic</button>
        <button className="px-3 py-1 bg-surface-container-high rounded hover:bg-surface-container-highest transition-colors" onClick={() => setTask('Analyze CSV')}>Analyze CSV</button>
        <button className="px-3 py-1 bg-surface-container-high rounded hover:bg-surface-container-highest transition-colors" onClick={() => setTask('Train a model')}>Train a model</button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background font-body-md text-on-surface antialiased flex flex-col">
      <TopBar
        task={task}
        loading={loading}
        handleCenterSubmit={handleCenterSubmit}
        handleFileChange={handleFileChange}
        file={file}
        error={error}
        setTask={setTask}
      />
      <div className="flex flex-1">
        <NavigationSidebar />
        <main className="flex-1 flex flex-col overflow-y-auto p-6 gap-6 bg-surface-container-lowest">
          {renderOperationStrip()}
          
          <section className="bg-surface-container rounded-md border border-outline-variant/30 shadow-sm p-6 relative overflow-hidden group">
            <form onSubmit={handleCenterSubmit} className="flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <label className="font-headline-sm font-medium text-on-surface">Orchestrate Pipeline</label>
                <span className="font-body-sm text-outline">Press ⌘K for command palette</span>
              </div>
              <div className="flex gap-2">
                <textarea
                  data-testid="task-composer"
                  placeholder="Enter task description or query..."
                  className="task-input"
                  value={task}
                  onChange={(e) => setTask(e.target.value)}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="task-button"
                >
                  {loading ? 'Running...' : 'Dispatch'}
                </button>
              </div>
              {error && <p className="text-error font-body-sm">{error}</p>}
            </form>
          </section>

          {loading && (
            <section className="bg-surface-container-low border border-primary/30 rounded-md p-5 shadow-sm relative">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse shadow-[0_0_8px_rgba(172,199,255,0.6)]" />
                  <h2 className="font-headline-sm font-semibold truncate max-w-sm sm:max-w-md">{task || file?.name || 'Processing...'}</h2>
                </div>
                <span className="font-body-sm px-2 py-1 rounded bg-primary/10 text-primary border border-primary/20">{loading ? 'Running' : (Object.keys(state.tasks)[0] && state.tasks[Object.keys(state.tasks)[0]].status) || 'Completed'}</span>
              </div>
              <div className="w-full bg-surface-container-highest h-1.5 rounded overflow-hidden mb-4">
                <div className="bg-primary h-full transition-all duration-300" style={{ width: `${Math.min(100, activity.length * 25)}%` }} />
              </div>
              <div className="flex flex-col gap-2 font-body-sm">
                {activity.map((act, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-outline">
                    <span className={`w-1.5 h-1.5 rounded-full ${act.status === 'done' ? 'bg-primary' : 'bg-primary animate-ping'}`} />
                    <span>{act.text}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          <div className="flex-1 flex flex-col gap-4">
            <h3 className="font-headline-sm font-medium text-on-surface">Execution Graph</h3>
            {Object.keys(state.tasks).length > 0 || state.history.length > 0 ? (
              <ExecutionGraph tasks={state.tasks} />
            ) : (
              renderEmptyState()
            )}
            {/* Result display */}
           {!loading && state.history[0] && (
  <>
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
      className="mt-4"
    >
      <div className="bg-surface-container rounded-md p-6">
        <h3 className="font-headline-sm font-medium text-on-surface">Result</h3>
        <pre className="mt-2 text-on-surface bg-surface-container-low p-4 rounded whitespace-pre-wrap break-words">
          {state.history[0].result?.result || 'No result'}
        </pre>
      </div>
    </motion.div>
    <ul className="mt-2 space-y-2">
      {state.history.slice(1).map((h, idx) => (
        <li key={idx} className="text-sm text-on-surface">
          <div className="flex justify-between">
            <span className="font-medium">{h.task || 'Task'}</span>
            <span className="text-outline">{h.status}</span>
          </div>
          <div className="text-xs text-outline">{new Date(h.timestamp).toLocaleString()}</div>
          <pre className="mt-1 whitespace-pre-wrap break-words bg-surface-container-low p-2 rounded">
            {h.result?.result || ''}
          </pre>
        </li>
      ))}
    </ul>
  </>
)}
          </div>
        </main>
      </div>

      {showCmdK && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface-container border border-outline-variant/40 rounded-lg max-w-lg w-full p-6 shadow-2xl">
            <h3 className="font-headline-sm font-semibold mb-4 text-on-surface">Command Palette</h3>
            <form onSubmit={handleCmdKSubmit} className="flex flex-col gap-4">
              <input
                ref={cmdKInputRef}
                type="text"
                value={cmdKTask}
                onChange={(e) => setCmdKTask(e.target.value)}
                placeholder="Type a quick command or query..."
                className="w-full bg-surface-container-high border border-outline-variant/40 rounded px-4 py-3 text-on-surface focus:outline-none focus:border-primary"
              />
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowCmdK(false)}
                  className="px-4 py-2 bg-surface-container-high text-on-surface rounded hover:bg-surface-container-highest"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-on-primary rounded hover:bg-primary/90"
                >
                  Execute
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default AppShell;
