const puppeteer = require('puppeteer');
(async () => {
  const url = 'http://localhost:5176/';
  const browser = await puppeteer.launch({headless: true, args: ['--no-sandbox','--disable-setuid-sandbox']});
  const page = await browser.newPage();
  const logs = [];
  page.on('console', msg => logs.push('PAGE CONSOLE: ' + msg.text()));
  page.on('pageerror', err => logs.push('PAGE ERROR: ' + err.message));
  try {
    await page.goto(url, {waitUntil: 'networkidle2'});
    await page.waitForTimeout(3000);
    const screenshotPath = 'C:/Users/LENOVO/.gemini/antigravity-ide/brain/2c81d369-6e96-46e4-9aee-958e273fbc0f/orbit-final.png';
    await page.screenshot({path: screenshotPath, fullPage:true});
    console.log(JSON.stringify({consoleLogs: logs, screenshotPath}));
  } catch(e){
    console.log('NAVIGATION ERROR:', e.message);
  }
  await browser.close();
})();
