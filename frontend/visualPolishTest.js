// visualPolishTest.js
const puppeteer = require('puppeteer-core');
const fs = require('fs');
(async () => {
  const chromePath = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  const browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: true,
    defaultViewport: null,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  const consoleErrors = [];
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  try {
    await page.goto('http://localhost:5173/', { waitUntil: 'networkidle2' });
    await page.waitForSelector('input[placeholder="Enter task description or query..."]', { timeout: 5000 });
    await page.type('input[placeholder="Enter task description or query..."]', 'Analyze how multi-agent AI systems improve software development.');
    await page.click('button:has-text("Dispatch")');
    await page.waitForFunction(() => {
      const pre = document.querySelector('pre');
      return pre && pre.innerText.includes('Mocked result data');
    }, { timeout: 20000 });
    await page.screenshot({ path: 'C:/Users/LENOVO/.gemini/antigravity-ide/brain/d6e3ff2f-00a7-4458-bf0f-cde66affec7f/visual_polish_screenshot.png', fullPage: true });
    fs.writeFileSync('console_errors.txt', consoleErrors.join('\n'));
    console.log('PASS');
  } catch (e) {
    console.error('FAIL', e);
    process.exit(1);
  } finally {
    await browser.close();
  }
})();
