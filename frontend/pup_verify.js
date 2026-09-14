const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('http://localhost:5175');
  await page.waitForSelector('.task-input', { timeout: 10000 });
  const task = 'Analyze how multi-agent AI systems can improve software development.';
  await page.type('.task-input', task);
  await page.click('.task-button');
  // Wait for result containing mocked data
  await page.waitForFunction(() => {
    const pre = document.querySelector('pre');
    return pre && pre.textContent.includes('Mocked result data');
  }, { timeout: 20000 });
  console.log('Result reveal verification: PASS');
  await browser.close();
})();
