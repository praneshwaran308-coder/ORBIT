import React from 'react';
import { useExecution } from '../context/ExecutionContext';
import AgentNode from './AgentNode';
import ExecutionEdge from './ExecutionEdge';
import { motion } from 'framer-motion';

// Positions for nodes (relative container)
const NODE_POSITIONS = {
  ORCHESTRATOR: { top: 20, left: '50%', translateX: '-50%' },
  RESEARCH: { top: 120, left: '25%', translateX: '-50%' },
  ANALYSIS: { top: 120, left: '50%', translateX: '-50%' },
  CODE: { top: 120, left: '75%', translateX: '-50%' },
  SYNTHESIS: { top: 220, left: '50%', translateX: '-50%' },
  RESULT: { top: 320, left: '50%', translateX: '-50%' },
};

const EDGES = [
  { from: 'ORCHESTRATOR', to: 'RESEARCH' },
  { from: 'ORCHESTRATOR', to: 'ANALYSIS' },
  { from: 'ORCHESTRATOR', to: 'CODE' },
  { from: 'RESEARCH', to: 'SYNTHESIS' },
  { from: 'ANALYSIS', to: 'SYNTHESIS' },
  { from: 'CODE', to: 'SYNTHESIS' },
  { from: 'SYNTHESIS', to: 'RESULT' },
];

export default function ExecutionGraph() {
  const { state } = useExecution();
  // Determine the current active task (if any)
  const activeTask = Object.values(state.tasks)[0] || state.history[0] || null;
  const agents = activeTask?.agents || {};

  // Determine activation for edges based on agent status
  const edgeActive = (from, to) => {
    const fromStatus = agents[from]?.status || 'idle';
    const toStatus = agents[to]?.status || 'idle';
    // Edge is active when both nodes have started (not idle)
    return fromStatus !== 'idle' && toStatus !== 'idle';
  };


  return (
    <div className="relative w-full h-[400px] my-8 bg-surface-container-low rounded" style={{ minHeight: '400px' }}>
      {/* SVG connections */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none">
        {EDGES.map((e, i) => (
          <ExecutionEdge
            key={i}
            fromPos={NODE_POSITIONS[e.from]}
            toPos={NODE_POSITIONS[e.to]}
            active={edgeActive(e.from, e.to)}
          />
        ))}
      </svg>
      {/* Nodes */}
      {Object.entries(NODE_POSITIONS).map(([name, pos]) => (
        <AgentNode
          key={name}
          name={name}
          position={pos}
          status={agents[name]?.status || 'idle'}
        />
      ))}
    </div>
  );
}
