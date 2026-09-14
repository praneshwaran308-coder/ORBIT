import React from 'react';
import { ExecutionProvider } from './context/ExecutionContext';
import AppShell from './components/AppShell';

function App() {
  return (
    <ExecutionProvider>
      <AppShell />
    </ExecutionProvider>
  );
}

export default App;
