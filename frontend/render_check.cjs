const puppeteer = require('puppeteer-core');
(async () => {
  const url = 'http://localhost:5177/';
  const execPath = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
  const browser = await puppeteer.launch({
    headless: true,
    executablePath: execPath,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  const logs = [];
  page.on('console', msg => logs.push('CONSOLE: ' + msg.type() + ' ' + msg.text()));
  page.on('pageerror', err => logs.push('PAGE ERROR: ' + err.message));
  page.on('requestfailed', req => logs.push('REQUEST FAILED: ' + req.url() + ' - ' + (req.failure()?.errorText || '')));
  try {
    await page.goto(url, {waitUntil: 'networkidle2', timeout: 30000});
    const title = await page.title();
    logs.push('TITLE: ' + title);
    const rootText = await page.$eval('#root', el => el.innerText);
    logs.push('ROOT TEXT: ' + rootText.slice(0, 200));
    const screenshotPath = 'C:/Users/LENOVO/.gemini/antigravity-ide/brain/2c81d369-6e96-46e4-9aee-958e273fbc0f/orbit-final.png';
    await page.screenshot({path: screenshotPath, fullPage: true});
    console.log(JSON.stringify({consoleLogs: logs, screenshotPath}));
  } catch (e) {
    console.log('SCRIPT ERROR:', e.message);
  }
  await browser.close();
})();
