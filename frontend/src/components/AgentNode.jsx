import React from 'react';
import { motion } from 'framer-motion';

// status: idle, running, thinking, completed, failed
export default function AgentNode({ name, position, status }) {
  const baseClasses = 'absolute flex flex-col items-center justify-center w-24 h-24 bg-surface-container rounded text-center text-sm font-medium text-on-surface';
  const statusClasses = {
    idle: 'bg-surface-container-low',
    running: 'bg-primary text-on-primary',
    thinking: 'bg-secondary text-on-secondary',
    completed: 'bg-success text-on-success',
    failed: 'bg-error text-on-error',
  }[status] || 'bg-surface-container-low';

  // animation variants
  const variants = {
    idle: { scale: 1 },
    running: { scale: [1, 1.05, 1], transition: { duration: 1.2, repeat: Infinity } },
    thinking: { opacity: [1, 0.5, 1], transition: { duration: 1.5, repeat: Infinity } },
    completed: { opacity: [0, 1], transition: { duration: 0.5 } },
    failed: { x: [0, -5, 5, -5, 5, 0], transition: { duration: 0.5 } },
  };

  const style = {
    top: position.top,
    left: position.left,
    transform: `translateX(${position.translateX})`,
  };

  return (
    <motion.div
      className={`${baseClasses} ${statusClasses}`}
      style={style}
      variants={variants}
      initial="idle"
      animate={status}
    >
      {name}
    </motion.div>
  );
}
