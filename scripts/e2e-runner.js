// scripts/e2e-runner.js
// This script starts the backend FastAPI server and the Vite dev server,
// waits for both to become healthy, then runs the authoritative Puppeteer E2E test.
// It ensures no arbitrary sleep – it polls HTTP endpoints with a timeout.
// After the test completes (success or failure), it shuts down the spawned processes.

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const https = require('https');

function httpGet(url) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http;
    const req = lib.get(url, (res) => {
      const { statusCode } = res;
      // consume response data to free memory
      res.resume();
      resolve(statusCode);
    });
    req.on('error', reject);
  });
}

async function waitForUrl(url, timeoutMs = 30000, intervalMs = 500) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const code = await httpGet(url);
      if (code >= 200 && code < 400) return true;
    } catch (_) {}
    await new Promise(r => setTimeout(r, intervalMs));
  }
  return false;
}

// Start backend FastAPI server
const backend = spawn('python', ['-m', 'uvicorn', 'backend.main:app', '--host', '127.0.0.1', '--port', '8000'], {
  cwd: path.resolve(__dirname, '..'),
  stdio: ['ignore', 'pipe', 'pipe']
});
backend.stdout.on('data', data => console.log(`[backend] ${data}`));
backend.stderr.on('data', data => console.error(`[backend ERR] ${data}`));

// Start Vite dev server on a dedicated port
const dev = spawn('npm', ['run', 'dev', '--', '--port', '5199'], {
  cwd: process.cwd(),
  shell: true,
  stdio: ['ignore', 'pipe', 'pipe']
});
let frontendUrl = 'http://localhost:5199';
let portDetected = true;

dev.stdout.on('data', data => {
  const line = data.toString();
  console.log(`[vite] ${line.trim()}`);
  const match = line.match(/http:\/\/localhost:(\d+)/);
  if (match && !portDetected) {
    const port = match[1];
    frontendUrl = `http://localhost:${port}`;
    portDetected = true;
    console.log(`[info] Detected Vite port ${port}`);
  }
});

dev.stderr.on('data', data => console.error(`[vite ERR] ${data}`));

function cleanupAndExit(code) {
  if (backend && !backend.killed) backend.kill();
  if (dev && !dev.killed) dev.kill();
  process.exit(code);
}
process.on('SIGINT', () => cleanupAndExit(1));
process.on('SIGTERM', () => cleanupAndExit(1));

(async () => {
  // Wait for backend health endpoint
  const backendReady = await waitForUrl('http://127.0.0.1:8000/health', 30000);
  if (!backendReady) {
    console.error('Backend did not become ready in time');
    cleanupAndExit(1);
  }
  console.log('[info] Backend ready');

  // Wait for Vite port detection then URL readiness
  const maxDetect = 30000;
  const startDetect = Date.now();
  while (!frontendUrl && Date.now() - startDetect < maxDetect) {
    await new Promise(r => setTimeout(r, 200));
  }
  if (!frontendUrl) {
    console.error('Failed to detect Vite dev server port');
    cleanupAndExit(1);
  }
  const frontendReady = await waitForUrl(`${frontendUrl}`, 30000);
  if (!frontendReady) {
    console.error('Frontend dev server not responding');
    cleanupAndExit(1);
  }
  console.log('[info] Frontend ready at', frontendUrl);

  // Run the authoritative puppeteer test
  const testEnv = Object.assign({}, process.env, {
    FRONTEND_URL: frontendUrl,
    BACKEND_URL: 'http://127.0.0.1:8000'
  });
  const test = spawn('node', ['tests/e2e.puppeteer.js'], {
    cwd: process.cwd(),
    env: testEnv,
    stdio: 'inherit'
  });
  test.on('close', code => {
    console.log(`[test] exited with code ${code}`);
    cleanupAndExit(code);
  });
})();
