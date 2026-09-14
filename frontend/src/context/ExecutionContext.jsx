import React, { createContext, useReducer, useContext } from 'react';

// Action types for the execution state machine
const ACTIONS = {
  START_TASK: 'START_TASK',
  UPDATE_AGENT: 'UPDATE_AGENT',
  LOG_EVENT: 'LOG_EVENT',
  COMPLETE_TASK: 'COMPLETE_TASK',
  FAIL_TASK: 'FAIL_TASK',
};

// Initial global state
const initialState = {
  tasks: {}, // taskId => { id, description, status, agents, logs, startTime, endTime }
  agents: {
    ORCHESTRATOR: { name: 'ORCHESTRATOR', status: 'idle' },
    RESEARCH: { name: 'RESEARCH', status: 'idle' },
    ANALYSIS: { name: 'ANALYSIS', status: 'idle' },
    CODE: { name: 'CODE', status: 'idle' },
    SYNTHESIS: { name: 'SYNTHESIS', status: 'idle' },
  },
  activityLog: [], // { timestamp, source, message, status }
  history: [], // completed tasks for session persistence
};

function reducer(state, action) {
  switch (action.type) {
    case ACTIONS.START_TASK: {
      const { taskId, description } = action.payload;
      const newTask = {
        id: taskId,
        description,
        status: 'queued',
        agents: {},
        logs: [],
        startTime: Date.now(),
        endTime: null,
      };
      return {
        ...state,
        tasks: { ...state.tasks, [taskId]: newTask },
        activityLog: [...state.activityLog, { timestamp: new Date(), source: 'SYSTEM', message: `Task ${taskId} queued`, status: 'queued' }],
      };
    }
    case ACTIONS.UPDATE_AGENT: {
      const { taskId, agentName, status } = action.payload;
      const task = state.tasks[taskId];
      if (!task) return state;
      const updatedAgents = { ...task.agents, [agentName]: { status } };
      const updatedTask = { ...task, agents: updatedAgents };
      return {
        ...state,
        tasks: { ...state.tasks, [taskId]: updatedTask },
        agents: { ...state.agents, [agentName]: { ...state.agents[agentName], status } },
        activityLog: [...state.activityLog, { timestamp: new Date(), source: agentName, message: `${agentName} ${status}`, status }],
      };
    }
    case ACTIONS.LOG_EVENT: {
      const { taskId, source, message, status } = action.payload;
      const task = state.tasks[taskId];
      if (!task) return state;
      const newLog = { timestamp: new Date(), source, message, status };
      const updatedTask = { ...task, logs: [...task.logs, newLog] };
      return {
        ...state,
        tasks: { ...state.tasks, [taskId]: updatedTask },
        activityLog: [...state.activityLog, newLog],
      };
    }
    case ACTIONS.COMPLETE_TASK: {
      const { taskId, result } = action.payload;
      const task = state.tasks[taskId];
      if (!task) return state;
      const completedTask = { ...task, status: 'completed', endTime: Date.now(), result };
      const { [taskId]: _, ...remainingTasks } = state.tasks;
      const historyEntry = { ...completedTask, duration: (completedTask.endTime - completedTask.startTime) / 1000 };
      return {
        ...state,
        tasks: remainingTasks,
        history: [historyEntry, ...state.history],
        activityLog: [...state.activityLog, { timestamp: new Date(), source: 'SYSTEM', message: `Task ${taskId} completed`, status: 'completed' }],
      };
    }
    case ACTIONS.FAIL_TASK: {
      const { taskId, error } = action.payload;
      const task = state.tasks[taskId];
      if (!task) return state;
      const failedTask = { ...task, status: 'failed', endTime: Date.now(), error };
      const { [taskId]: _, ...remainingTasks } = state.tasks;
      const historyEntry = { ...failedTask, duration: (failedTask.endTime - failedTask.startTime) / 1000 };
      return {
        ...state,
        tasks: remainingTasks,
        history: [historyEntry, ...state.history],
        activityLog: [...state.activityLog, { timestamp: new Date(), source: 'SYSTEM', message: `Task ${taskId} failed: ${error}`, status: 'failed' }],
      };
    }
    default:
      return state;
  }
}

const ExecutionContext = createContext(null);

export function ExecutionProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Helper actions exposed to components
  const startTask = (taskId, description) => {
    dispatch({ type: ACTIONS.START_TASK, payload: { taskId, description } });
  };

  const updateAgent = (taskId, agentName, status) => {
    dispatch({ type: ACTIONS.UPDATE_AGENT, payload: { taskId, agentName, status } });
  };

  const logEvent = (taskId, source, message, status) => {
    dispatch({ type: ACTIONS.LOG_EVENT, payload: { taskId, source, message, status } });
  };

  const completeTask = (taskId, result) => {
    dispatch({ type: ACTIONS.COMPLETE_TASK, payload: { taskId, result } });
  };

  const failTask = (taskId, error) => {
    dispatch({ type: ACTIONS.FAIL_TASK, payload: { taskId, error } });
  };

  return (
    <ExecutionContext.Provider value={{ state, startTask, updateAgent, logEvent, completeTask, failTask }}>
      {children}
    </ExecutionContext.Provider>
  );
}

export function useExecution() {
  const context = useContext(ExecutionContext);
  if (!context) {
    throw new Error('useExecution must be used within ExecutionProvider');
  }
  return context;
}
