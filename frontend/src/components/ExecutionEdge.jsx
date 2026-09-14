import React from 'react';
import { motion } from 'framer-motion';

// Props: fromPos, toPos (objects with top, left (percentage string), translateX), active (bool)
// Simple conversion: assume container width 1000 units for percentage
function computePoint(pos) {
  const leftPercent = parseFloat(pos.left);
  const x = (leftPercent / 100) * 1000; // map to 0-1000
  const y = pos.top;
  return { x, y };
}

export default function ExecutionEdge({ fromPos, toPos, active }) {
  const start = computePoint(fromPos);
  const end = computePoint(toPos);
  const length = Math.hypot(end.x - start.x, end.y - start.y);
  const dashArray = `${length}`;

  const variants = {
    inactive: { strokeDashoffset: length },
    active: { strokeDashoffset: 0, transition: { duration: 0.5 } },
  };

  return (
    <motion.line
      x1={start.x}
      y1={start.y}
      x2={end.x}
      y2={end.y}
      stroke="var(--color-primary)"
      strokeWidth="4"
      strokeLinecap="round"
      strokeDasharray={dashArray}
      variants={variants}
      initial="inactive"
      animate={active ? 'active' : 'inactive'}
    />
  );
}
