// frontend/tests/e2e.puppeteer.js
// Puppeteer end‑to‑end test that validates the real FastAPI backend integration.
// Run with: npm test

import puppeteer from 'puppeteer-core';

(async () => {
  const chromePath = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();

  const networkLogs = [];
  let consoleError = false;

  page.on('response', async (response) => {
    const request = response.request();
    const url = request.url();
    const method = request.method();
    let body = null;
    try { body = await response.json(); } catch (e) {}
    networkLogs.push({ url, method, status: response.status(), body });
  });

  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleError = true;
      console.error('Console error:', msg.text());
    }
  });

  // Open frontend (vite dev server)
  const frontendUrl = process.env.FRONTEND_URL || 'http://localhost:5175';
  await page.goto(frontendUrl, { waitUntil: 'load' });

  // Locate task composer textarea (robust selector based on placeholder)
  const textareaSelector = '[data-testid="task-composer"]';
  await page.waitForSelector(textareaSelector, { timeout: 10000 });
  const taskText = 'Analyze how multi‑agent AI systems improve software development.';
  await page.type(textareaSelector, taskText);

  // Click Dispatch button (by text content)
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(
      (b) => b.textContent.trim() === 'Dispatch'
    );
    if (btn) btn.click();
  });

  // Capture POST /run response and extract real task_id
  let taskId = null;
  const waitForRun = async () => {
    const start = Date.now();
    while (!taskId && Date.now() - start < 15000) {
      for (const entry of networkLogs) {
        if (entry.method === 'POST' && /\/run$/.test(entry.url) && entry.body && entry.body.task_id) {
          taskId = entry.body.task_id;
          console.log('Detected task_id:', taskId);
          break;
        }
      }
      await new Promise(r => setTimeout(r, 200));
    }
  };
  await waitForRun();
  if (!taskId) {
    console.error('Failed to detect POST /run with task_id');
    process.exit(1);
  }

  // Poll GET /status/<task_id> until completed
  const waitForCompletion = async () => {
    const start = Date.now();
    while (Date.now() - start < 30000) {
      for (const entry of networkLogs) {
        if (
          entry.method === 'GET' &&
          new RegExp(`/status/${taskId}$`).test(entry.url) &&
          entry.body && entry.body.status === 'completed'
        ) {
          return entry.body;
        }
      }
      await new Promise(r => setTimeout(r, 500));
    }
    return null;
  };
  const finalStatus = await waitForCompletion();
  if (!finalStatus) {
    console.error('Task did not reach completed status within timeout');
    process.exit(1);
  }

  // UI assertions: rely on result and history checks after task completion

  // Result section (any pre or element with role='region')
  const resultSelector = 'pre, [role="region"]';
  await page.waitForSelector(resultSelector, { timeout: 20000 });
  const resultText = await page.$eval(resultSelector, el => el.textContent.trim());
  if (!resultText) {
    console.error('Result section is empty');
    process.exit(1);
  }


  // Ensure no console errors
  if (consoleError) {
    console.error('Console errors detected during test');
    process.exit(1);
  }

  console.log('E2E REAL BACKEND: PASS');
  await browser.close();
  process.exit(0);
})();
