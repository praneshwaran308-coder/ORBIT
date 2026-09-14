// e2e_verify.js - Puppeteer script for ORBIT real backend integration verification
const puppeteer = require('puppeteer');

(async () => {
  const chromePath = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });
  const page = await browser.newPage();

  const networkResponses = [];
  page.on('response', async resp => {
    try {
      const json = await resp.json();
      networkResponses.push({url: resp.url(), status: resp.status(), json});
    } catch (e) {
      // ignore non-JSON
    }
  });

  // Vite dev server observed on port 5176 (adjust if different)
  const targetUrl = 'http://localhost:5176/';
  await page.goto(targetUrl, {waitUntil: 'networkidle2'});

  const taskText = 'Analyze how multi-agent AI systems can improve software development.';
  await page.waitForSelector('.task-input');
  await page.type('.task-input', taskText);
  await page.click('button.task-button');

  // Capture POST /run and obtain task_id
  let postRun;
  while (!postRun) {
    postRun = networkResponses.find(r => r.url.includes('/run') && r.json && r.json.task_id);
    await new Promise(r => setTimeout(r, 100));
  }
  const taskId = postRun.json.task_id;
  console.log('POST /run task_id:', taskId);

  // Poll status until completed
  let completed = false;
  let lastStatus = null;
  while (!completed) {
    await new Promise(r => setTimeout(r, 800));
    // Find latest GET /status for this taskId
    const statusResp = networkResponses.find(r => r.url.includes(`/status/${taskId}`) && r.json && r.json.status);
    if (statusResp) {
      completed = statusResp.json.status === 'completed';
      lastStatus = statusResp.json;
    }
  }
  console.log('Task completed. Final status:', lastStatus);

  // Verify UI result matches backend result
  const uiResult = await page.$eval('pre', el => el.textContent.trim()).catch(() => '');
  const backendResult = (lastStatus && lastStatus.result && lastStatus.result.result) || '';
  console.log('UI result matches backend?', uiResult === backendResult);

  // Verify activity appears in UI
  const activityExists = await page.$$eval('.activity-strip, .activity', els => els.length > 0);
  console.log('Activity present:', activityExists);

  // Refresh page and verify result persists (history)
  await page.reload({waitUntil: 'networkidle2'});
  const refreshedResult = await page.$eval('pre', el => el.textContent.trim()).catch(() => null);
  console.log('Result after refresh exists:', !!refreshedResult);

  await browser.close();

  // Emit summary JSON for automated parsing
  console.log(JSON.stringify({
    postRunTaskId: taskId,
    completed,
    uiResultMatchesBackend: uiResult === backendResult,
    activityExists,
    resultAfterRefresh: !!refreshedResult,
  }));
})();
